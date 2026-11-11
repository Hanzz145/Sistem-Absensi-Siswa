# Sistem Absensi Siswa — SMA Cendekia

Aplikasi absensi siswa sederhana dengan **Streamlit + SQLite**, tanpa login.
Tugas UTS Kelompok 6.

## Fitur

- **Catat absensi** per kelas dan tanggal, status Hadir / Sakit / Izin / Alpa / Terlambat, plus keterangan opsional.
- **Riwayat absensi** dengan filter kelas, rentang tanggal, NIS, dan nama; hapus catatan dengan konfirmasi.
- **Rekap harian** dan **laporan bulanan** per kelas (jumlah tiap status dan grafik).
- **Data siswa**: tambah, ubah, hapus (ditolak jika masih punya riwayat absensi).
- **Data kelas**: tambah, hapus (ditolak jika masih punya siswa).
- Absensi ganda untuk NIS + tanggal yang sama dicegah oleh constraint `UNIQUE(nis, tanggal)`.
- Data contoh otomatis dibuat saat pertama dijalankan.

## Menjalankan

Virtual environment dan dependensi sudah disiapkan di folder ini.

```bash
# Windows
venv\Scripts\activate
streamlit run absensi_siswa.py
```

Buka **http://localhost:8501**.

Jika venv belum ada:

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

## Struktur Database (`absensi_siswa.db`)

| Tabel | Kolom |
|---|---|
| `kelas` | `id_kelas` (PK), `nama_kelas` (UNIQUE), `tingkat` |
| `siswa` | `nis` (PK), `nama_siswa`, `jenis_kelamin` (L/P), `id_kelas` (FK) |
| `absensi` | `id_absensi` (PK), `nis` (FK), `tanggal` (YYYY-MM-DD), `status`, `keterangan` |

Constraint: `UNIQUE(nis, tanggal)`, `CHECK` status, foreign key dengan `ON DELETE RESTRICT`,
dan `PRAGMA foreign_keys = ON` pada setiap koneksi.

## Aturan utama

- NIS unik dan wajib diisi.
- Nama kelas unik dan wajib diisi.
- Satu siswa hanya punya satu catatan absensi per tanggal.
- Kelas yang masih memiliki siswa tidak dapat dihapus.
- Siswa yang masih memiliki riwayat absensi tidak dapat dihapus.
- Catatan absensi hanya dihapus setelah konfirmasi.
