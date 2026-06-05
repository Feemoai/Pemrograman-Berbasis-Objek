# model.py
import datetime


class Transaksi:
    """Merepresentasikan satu entitas transaksi pengeluaran."""

    def __init__(self, deskripsi: str, jumlah: float, kategori: str,
                 tanggal, id_transaksi: int = None):
        self.id = id_transaksi
        self.deskripsi = str(deskripsi) if deskripsi else "Tanpa Deskripsi"

        # validasi jumlah
        try:
            jumlah_float = float(jumlah)
            self.jumlah = jumlah_float if jumlah_float > 0 else 0.0
            if jumlah_float <= 0:
                print(f"Peringatan: Jumlah '{jumlah}' harus positif.")
        except (ValueError, TypeError):
            self.jumlah = 0.0
            print(f"Peringatan: Jumlah '{jumlah}' tidak valid.")

        self.kategori = str(kategori) if kategori else "Lainnya"

        # validasi tanggal
        if isinstance(tanggal, datetime.date):
            self.tanggal = tanggal
        elif isinstance(tanggal, str):
            try:
                self.tanggal = datetime.datetime.strptime(tanggal, "%Y-%m-%d").date()
            except ValueError:
                self.tanggal = datetime.date.today()
                print(f"Peringatan: Format tanggal '{tanggal}' salah.")
        else:
            self.tanggal = datetime.date.today()
            print(f"Peringatan: Tipe tanggal '{type(tanggal)}' tidak valid.")

    def __repr__(self) -> str:
        return (f"Transaksi(ID:{self.id}, "
                f"Tgl:{self.tanggal.strftime('%Y-%m-%d')}, "
                f"Jml:{self.jumlah:.0f}, "
                f"Kat:'{self.kategori}', "
                f"Desc:'{self.deskripsi}')")

    def to_dict(self) -> dict:
        return {
            "deskripsi": self.deskripsi,
            "jumlah": self.jumlah,
            "kategori": self.kategori,
            "tanggal": self.tanggal.strftime("%Y-%m-%d")
        }
