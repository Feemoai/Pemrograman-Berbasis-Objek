# manajer_anggaran.py
import datetime
import pandas as pd
from model import Transaksi
import database


def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")


class AnggaranHarian:
    """Mengelola logika bisnis pengeluaran harian."""

    _db_setup_done = False  # flag agar setup DB hanya dijalankan sekali

    def __init__(self):
        if not AnggaranHarian._db_setup_done:
            print("[AnggaranHarian] Melakukan pengecekan/setup database awal...")
            if database.setup_database_initial():
                AnggaranHarian._db_setup_done = True
                print("[AnggaranHarian] Database siap.")
            else:
                print("[AnggaranHarian] KRITICAL: Setup database awal GAGAL!")

    def tambah_transaksi(self, transaksi: Transaksi) -> bool:
        """Menyimpan transaksi baru ke database."""
        if not isinstance(transaksi, Transaksi) or transaksi.jumlah <= 0:
            return False
        sql = "INSERT INTO transaksi (deskripsi, jumlah, kategori, tanggal) VALUES (?, ?, ?, ?)"
        params = (
            transaksi.deskripsi,
            transaksi.jumlah,
            transaksi.kategori,
            transaksi.tanggal.strftime("%Y-%m-%d")
        )
        last_id = database.execute_query(sql, params)
        if last_id is not None:
            transaksi.id = last_id
            return True
        return False

    
    # PENUGASAN: Hapus Transaksi
    def hapus_transaksi(self, id_transaksi: int) -> bool:
        """Menghapus transaksi berdasarkan ID dari database."""
        sql = "DELETE FROM transaksi WHERE id = ?"
        result = database.execute_query(sql, (id_transaksi,))
        if result is not None:
            # reset urutan ID jika tabel sudah kosong
            self._reset_id_jika_kosong()
            return True
        return False

    def _reset_id_jika_kosong(self):
        """Reset urutan AUTOINCREMENT jika tabel transaksi sudah kosong."""
        cek = database.fetch_query(
            "SELECT COUNT(*) FROM transaksi", fetch_all=False
        )
        if cek and cek[0] == 0:
            # hapus record di sqlite_sequence agar ID mulai dari 1 lagi
            database.execute_query(
                "DELETE FROM sqlite_sequence WHERE name = 'transaksi'"
            )
    # Batas kode penugasan sampai sini
    
    def get_semua_transaksi_obj(self) -> list:
        """Mengambil semua transaksi sebagai list objek Transaksi."""
        sql = "SELECT id, deskripsi, jumlah, kategori, tanggal FROM transaksi ORDER BY tanggal DESC, id DESC"
        rows = database.fetch_query(sql, fetch_all=True)
        transaksi_list = []
        if rows:
            for row in rows:
                transaksi_list.append(Transaksi(
                    id_transaksi=row['id'],
                    deskripsi=row['deskripsi'],
                    jumlah=row['jumlah'],
                    kategori=row['kategori'],
                    tanggal=row['tanggal']
                ))
        return transaksi_list

    def get_dataframe_transaksi(self, filter_tanggal: datetime.date = None) -> pd.DataFrame:
        """Mengambil transaksi sebagai DataFrame Pandas."""
        query = "SELECT id, tanggal, kategori, deskripsi, jumlah FROM transaksi"
        params = None
        if filter_tanggal:
            query += " WHERE tanggal = ?"
            params = (filter_tanggal.strftime("%Y-%m-%d"),)
        query += " ORDER BY tanggal DESC, id DESC"
        df = database.get_dataframe(query, params=params)
        if not df.empty:
            df['Jumlah (Rp)'] = df['jumlah'].map(lambda x: format_rupiah(x or 0))
            df = df[['id', 'tanggal', 'kategori', 'deskripsi', 'Jumlah (Rp)']]
        return df

    def hitung_total_pengeluaran(self, tanggal: datetime.date = None) -> float:
        """Menghitung total pengeluaran, bisa difilter per tanggal."""
        sql = "SELECT SUM(jumlah) FROM transaksi"
        params = None
        if tanggal:
            sql += " WHERE tanggal = ?"
            params = (tanggal.strftime("%Y-%m-%d"),)
        result = database.fetch_query(sql, params=params, fetch_all=False)
        if result and result[0] is not None:
            return float(result[0])
        return 0.0

    def get_pengeluaran_per_kategori(self, tanggal: datetime.date = None) -> dict:
        """Menghitung total pengeluaran per kategori."""
        hasil = {}
        sql = "SELECT kategori, SUM(jumlah) FROM transaksi"
        params = []
        if tanggal:
            sql += " WHERE tanggal = ?"
            params.append(tanggal.strftime("%Y-%m-%d"))
        sql += " GROUP BY kategori HAVING SUM(jumlah) > 0 ORDER BY SUM(jumlah) DESC"
        rows = database.fetch_query(sql, params=tuple(params) if params else None, fetch_all=True)
        if rows:
            for row in rows:
                kategori = row['kategori'] if row['kategori'] else "Lainnya"
                jumlah = float(row[1]) if row[1] is not None else 0.0
                hasil[kategori] = jumlah
        return hasil