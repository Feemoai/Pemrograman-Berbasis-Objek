# main_app.py
import streamlit as st
import datetime
import pandas as pd

try:
    from model import Transaksi
    from manajer_anggaran import AnggaranHarian
    from konfigurasi import KATEGORI_PENGELUARAN
except ImportError as e:
    st.error(f"Gagal mengimpor modul: {e}. Pastikan semua file .py ada di folder yang sama.")
    st.stop()


# helper format rupiah
def format_rp(angka):
    return f"Rp {angka or 0:,.0f}".replace(",", ".")


# konfigurasi halaman
st.set_page_config(
    page_title="Catatan Pengeluaran",
    layout="wide",
    initial_sidebar_state="expanded"
)


# inisialisasi AnggaranHarian - di-cache agar tidak dibuat ulang setiap rerun
@st.cache_resource
def get_anggaran_manager():
    print(">>> STREAMLIT: Menginisialisasi AnggaranHarian...")
    return AnggaranHarian()


anggaran = get_anggaran_manager()


# ================================================================
# HALAMAN 1: Tambah Pengeluaran
# ================================================================
def halaman_input(anggaran: AnggaranHarian):
    st.header("➕ Tambah Pengeluaran Baru")

    with st.form("form_transaksi_baru", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            deskripsi = st.text_input("Deskripsi*", placeholder="Contoh: Makan siang")
        with col2:
            kategori = st.selectbox("Kategori*:", KATEGORI_PENGELUARAN, index=0)

        col3, col4 = st.columns([1, 1])
        with col3:
            jumlah = st.number_input(
                "Jumlah (Rp)*:", min_value=0.01, step=1000.0,
                format="%.0f", value=None, placeholder="Contoh: 25000"
            )
        with col4:
            tanggal = st.date_input("Tanggal*:", value=datetime.date.today())

        submitted = st.form_submit_button("💾 Simpan Transaksi")

        if submitted:
            if not deskripsi:
                st.warning("⚠️ Deskripsi wajib diisi!")
            elif jumlah is None or jumlah <= 0:
                st.warning("⚠️ Jumlah wajib diisi dan harus lebih dari 0!")
            else:
                with st.spinner("Menyimpan..."):
                    tx = Transaksi(deskripsi, float(jumlah), kategori, tanggal)
                    if anggaran.tambah_transaksi(tx):
                        st.success("✅ Transaksi berhasil disimpan!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Gagal menyimpan transaksi.")


# ================================================================
# HALAMAN 2: Riwayat + Hapus Transaksi (PENUGASAN)
# ================================================================
def halaman_riwayat(anggaran: AnggaranHarian):
    st.subheader("📋 Riwayat Semua Transaksi")

    col_refresh, _ = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()

    with st.spinner("Memuat riwayat..."):
        df_transaksi = anggaran.get_dataframe_transaksi()

    if df_transaksi is None:
        st.error("Gagal mengambil riwayat.")
        return
    elif df_transaksi.empty:
        st.info("Belum ada transaksi yang tercatat.")
        return

    st.dataframe(df_transaksi, use_container_width=True, hide_index=True)

    # ---- PENUGASAN: Form Hapus Transaksi ----
    st.divider()
    st.subheader("🗑️ Hapus Transaksi")
    st.caption("Masukkan ID transaksi yang ingin dihapus (lihat kolom 'id' pada tabel di atas).")

    with st.form("form_hapus"):
        id_hapus = st.number_input(
            "ID Transaksi yang akan dihapus:",
            min_value=1, step=1, value=None,
            placeholder="Contoh: 3"
        )
        submit_hapus = st.form_submit_button("🗑️ Hapus Transaksi")

        if submit_hapus:
            if id_hapus is None:
                st.warning("⚠️ Masukkan ID transaksi terlebih dahulu.")
            else:
                id_hapus = int(id_hapus)
                # cek apakah ID ada di tabel
                id_list = df_transaksi['id'].tolist()
                if id_hapus not in id_list:
                    st.error(f"❌ ID {id_hapus} tidak ditemukan dalam daftar transaksi.")
                else:
                    # simpan id ke session_state untuk konfirmasi
                    st.session_state['id_konfirmasi'] = id_hapus
                    st.session_state['tampil_konfirmasi'] = True

    # konfirmasi hapus di luar form
    if st.session_state.get('tampil_konfirmasi', False):
        id_konfirmasi = st.session_state.get('id_konfirmasi')
        st.warning(f"⚠️ Yakin ingin menghapus transaksi ID **{id_konfirmasi}**? Tindakan ini tidak bisa dibatalkan.")

        col_ya, col_tidak = st.columns([1, 4])
        with col_ya:
            if st.button("✅ Ya, Hapus", type="primary"):
                with st.spinner("Menghapus..."):
                    berhasil = anggaran.hapus_transaksi(id_konfirmasi)
                if berhasil:
                    st.success(f"✅ Transaksi ID {id_konfirmasi} berhasil dihapus.")
                    st.session_state['tampil_konfirmasi'] = False
                    st.session_state['id_konfirmasi'] = None
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ Gagal menghapus transaksi.")
        with col_tidak:
            if st.button("❌ Batal"):
                st.session_state['tampil_konfirmasi'] = False
                st.session_state['id_konfirmasi'] = None
                st.rerun()
    # Batas Kode Penugasan

# ================================================================
# HALAMAN 3: Ringkasan
# ================================================================
def halaman_ringkasan(anggaran: AnggaranHarian):
    st.subheader("📊 Ringkasan Pengeluaran")

    col_filter, _ = st.columns([1, 2])
    with col_filter:
        pilihan_periode = st.selectbox(
            "Filter Periode:",
            ["Semua Waktu", "Hari Ini", "Pilih Tanggal"],
            key="filter_periode"
        )

    tanggal_filter = None
    label_periode = "(Semua Waktu)"

    if pilihan_periode == "Hari Ini":
        tanggal_filter = datetime.date.today()
        label_periode = f"({tanggal_filter.strftime('%d %b %Y')})"
    elif pilihan_periode == "Pilih Tanggal":
        tanggal_filter = st.date_input(
            "Pilih Tanggal:",
            value=datetime.date.today(),
            key="tanggal_pilihan"
        )
        label_periode = f"({tanggal_filter.strftime('%d %b %Y')})"

    # total pengeluaran
    @st.cache_data(ttl=300)
    def hitung_total_cached(tgl_filter):
        return anggaran.hitung_total_pengeluaran(tanggal=tgl_filter)

    total = hitung_total_cached(tanggal_filter)
    st.metric(label=f"Total Pengeluaran {label_periode}", value=format_rp(total))

    st.divider()
    st.subheader(f"Pengeluaran per Kategori {label_periode}")

    @st.cache_data(ttl=300)
    def get_kategori_cached(tgl_filter):
        return anggaran.get_pengeluaran_per_kategori(tanggal=tgl_filter)

    with st.spinner("Memuat ringkasan..."):
        dict_per_kategori = get_kategori_cached(tanggal_filter)

    if not dict_per_kategori:
        st.info("Tidak ada data untuk periode ini.")
    else:
        data_kategori = [{"Kategori": kat, "Total": jml} for kat, jml in dict_per_kategori.items()]
        df_kategori = (
            pd.DataFrame(data_kategori)
            .sort_values(by="Total", ascending=False)
            .reset_index(drop=True)
        )
        df_kategori['Total (Rp)'] = df_kategori['Total'].apply(format_rp)

        col_kat1, col_kat2 = st.columns(2)
        with col_kat1:
            st.write("Tabel:")
            st.dataframe(df_kategori[['Kategori', 'Total (Rp)']], hide_index=True, use_container_width=True)
        with col_kat2:
            st.write("Grafik:")
            st.bar_chart(df_kategori.set_index('Kategori')['Total'], use_container_width=True)


# ================================================================
# FUNGSI UTAMA
# ================================================================
def main():
    st.sidebar.title("🏦 Catatan Pengeluaran")
    menu_pilihan = st.sidebar.radio(
        "Pilih Menu:",
        ["Tambah", "Riwayat", "Ringkasan"],
        key="menu_utama"
    )
    st.sidebar.markdown("---")
    st.sidebar.info("Jobsheet - Aplikasi Keuangan")

    manajer = get_anggaran_manager()

    if menu_pilihan == "Tambah":
        halaman_input(manajer)
    elif menu_pilihan == "Riwayat":
        halaman_riwayat(manajer)
    elif menu_pilihan == "Ringkasan":
        halaman_ringkasan(manajer)

    st.markdown("---")
    st.caption("Pengembangan Aplikasi Berbasis OOP")


if __name__ == "__main__":
    main()
