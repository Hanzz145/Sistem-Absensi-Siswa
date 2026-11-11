# ============================================================
# Sistem Absensi Siswa — SMA Cendekia
# Streamlit + SQLite · Kelompok 6 · Tanpa login
# ============================================================
import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta

import pandas as pd
import streamlit as st

DB_PATH = "absensi_siswa.db"
STATUS = ["Hadir", "Sakit", "Izin", "Alpa", "Terlambat"]
BULAN = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

st.set_page_config(page_title="Sistem Absensi Siswa", page_icon="🏫", layout="wide")


# ---------------- Database ----------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def q(sql, params=()):
    with db() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def run(sql, params=()):
    with db() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid, cur.rowcount


def init_db():
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS kelas (
                id_kelas   INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_kelas TEXT NOT NULL UNIQUE,
                tingkat    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS siswa (
                nis            TEXT PRIMARY KEY,
                nama_siswa     TEXT NOT NULL,
                jenis_kelamin  TEXT NOT NULL CHECK (jenis_kelamin IN ('L', 'P')),
                id_kelas       INTEGER NOT NULL
                               REFERENCES kelas(id_kelas) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS absensi (
                id_absensi INTEGER PRIMARY KEY AUTOINCREMENT,
                nis        TEXT NOT NULL
                           REFERENCES siswa(nis) ON DELETE RESTRICT,
                tanggal    TEXT NOT NULL,
                status     TEXT NOT NULL
                           CHECK (status IN ('Hadir', 'Sakit', 'Izin', 'Alpa', 'Terlambat')),
                keterangan TEXT,
                UNIQUE (nis, tanggal)
            );
            """
        )

        if conn.execute("SELECT COUNT(*) FROM kelas").fetchone()[0] == 0:
            kelas = [("X-1", "X"), ("X-2", "X"), ("XI-1", "XI")]
            conn.executemany(
                "INSERT INTO kelas (nama_kelas, tingkat) VALUES (?, ?)", kelas
            )
            id_kelas = {
                r["nama_kelas"]: r["id_kelas"]
                for r in conn.execute("SELECT id_kelas, nama_kelas FROM kelas")
            }
            siswa = [
                ("1001", "Aditya Pratama", "L", "X-1"),
                ("1002", "Bunga Lestari", "P", "X-1"),
                ("1003", "Citra Ayu Ningsih", "P", "X-1"),
                ("1004", "Dimas Saputra", "L", "X-1"),
                ("1005", "Eka Putri Ramadhani", "P", "X-1"),
                ("1006", "Fajar Nugroho", "L", "X-1"),
                ("1007", "Gita Maharani", "P", "X-1"),
                ("1008", "Hendra Wijaya", "L", "X-1"),
                ("1009", "Indah Permata Sari", "P", "X-2"),
                ("1010", "Joko Susilo", "L", "X-2"),
                ("1011", "Kirana Dewi", "P", "X-2"),
                ("1012", "Lukman Hakim", "L", "X-2"),
                ("1013", "Maya Sari", "P", "X-2"),
                ("1014", "Naufal Rizky", "L", "X-2"),
                ("1015", "Olivia Rahmawati", "P", "X-2"),
                ("1016", "Putra Pratama", "L", "X-2"),
                ("1017", "Qori Amalia", "P", "XI-1"),
                ("1018", "Raka Maulana", "L", "XI-1"),
                ("1019", "Sinta Wulandari", "P", "XI-1"),
                ("1020", "Taufik Hidayat", "L", "XI-1"),
                ("1021", "Umi Kalsum", "P", "XI-1"),
                ("1022", "Vino Bastian", "L", "XI-1"),
                ("1023", "Wulan Sari", "P", "XI-1"),
                ("1024", "Yoga Pratama", "L", "XI-1"),
            ]
            conn.executemany(
                "INSERT INTO siswa (nis, nama_siswa, jenis_kelamin, id_kelas) "
                "VALUES (?, ?, ?, ?)",
                [(n, nm, jk, id_kelas[k]) for n, nm, jk, k in siswa],
            )

        # Data absensi contoh untuk dua hari sebelumnya (bukan hari ini)
        if conn.execute("SELECT COUNT(*) FROM absensi").fetchone()[0] == 0:
            semua_nis = [r["nis"] for r in conn.execute("SELECT nis FROM siswa ORDER BY nis")]
            contoh_status = [
                "Hadir", "Hadir", "Hadir", "Sakit", "Hadir", "Izin", "Terlambat", "Hadir",
            ]
            for selisih in (1, 2):
                tanggal = (date.today() - timedelta(days=selisih)).isoformat()
                for i, nis in enumerate(semua_nis):
                    status = contoh_status[i % len(contoh_status)]
                    ket = {
                        "Sakit": "Surat dokter",
                        "Izin": "Acara keluarga",
                        "Terlambat": "Datang 10 menit",
                    }.get(status)
                    conn.execute(
                        "INSERT OR IGNORE INTO absensi (nis, tanggal, status, keterangan) "
                        "VALUES (?, ?, ?, ?)",
                        (nis, tanggal, status, ket),
                    )


# ---------------- Utilitas UI ----------------
def flash(pesan, jenis="success"):
    st.session_state["_flash"] = (pesan, jenis)


def tampilkan_flash():
    item = st.session_state.pop("_flash", None)
    if item:
        pesan, jenis = item
        getattr(st, jenis)(pesan)


def daftar_kelas():
    return q(
        "SELECT id_kelas, nama_kelas, tingkat FROM kelas "
        "ORDER BY tingkat, nama_kelas"
    )


def label_kelas(k):
    return f"{k['nama_kelas']} (Tingkat {k['tingkat']})"


def opsi_kelas(kelas_list):
    return {label_kelas(k): k["id_kelas"] for k in kelas_list}


def bersihkan(teks):
    if teks is None or pd.isna(teks):
        return ""
    return str(teks).strip()


# ---------------- Halaman: Absensi ----------------
def halaman_absensi():
    st.title("📝 Catat Absensi")
    st.caption("Pilih kelas dan tanggal, lalu isi status kehadiran setiap siswa.")

    kelas_list = daftar_kelas()
    if not kelas_list:
        st.warning("Belum ada data kelas. Tambahkan kelas terlebih dahulu di menu Data Kelas.")
        return

    opsi = opsi_kelas(kelas_list)
    c1, c2 = st.columns(2)
    with c1:
        pilihan_kelas = st.selectbox("Kelas", list(opsi.keys()), key="abs_kelas")
    with c2:
        tanggal = st.date_input("Tanggal", value=date.today(), key="abs_tanggal")

    id_kelas = opsi[pilihan_kelas]
    tanggal_str = tanggal.isoformat()

    siswa = q(
        "SELECT nis, nama_siswa FROM siswa WHERE id_kelas = ? ORDER BY nama_siswa",
        (id_kelas,),
    )
    if not siswa:
        st.info("Belum ada siswa di kelas ini. Tambahkan siswa di menu Data Siswa.")
        return

    tersimpan = q(
        """
        SELECT a.nis, a.status, a.keterangan
        FROM absensi a
        JOIN siswa s ON s.nis = a.nis
        WHERE s.id_kelas = ? AND a.tanggal = ?
        """,
        (id_kelas, tanggal_str),
    )
    existing = {r["nis"]: r for r in tersimpan}

    if existing:
        st.info(
            f"{len(existing)} dari {len(siswa)} siswa sudah tercatat pada tanggal ini. "
            "Data yang sudah ada akan diperbarui, bukan dibuat ganda."
        )
    else:
        st.caption("Belum ada absensi untuk tanggal ini. Status awal: Hadir.")

    baris = []
    for s in siswa:
        lama = existing.get(s["nis"], {})
        baris.append(
            {
                "NIS": s["nis"],
                "Nama Siswa": s["nama_siswa"],
                "Status": lama.get("status", "Hadir"),
                "Keterangan": lama.get("keterangan") or "",
            }
        )

    edited = st.data_editor(
        pd.DataFrame(baris),
        hide_index=True,
        width="stretch",
        disabled=["NIS", "Nama Siswa"],
        column_order=["Nama Siswa", "Status", "Keterangan", "NIS"],
        column_config={
            "NIS": st.column_config.TextColumn("NIS", width="small"),
            "Nama Siswa": st.column_config.TextColumn("Nama Siswa", width="medium"),
            "Status": st.column_config.SelectboxColumn(
                "Status", options=STATUS, required=True, width="small"
            ),
            "Keterangan": st.column_config.TextColumn(
                "Keterangan (opsional)", width="medium"
            ),
        },
        key=f"editor_absensi_{id_kelas}_{tanggal_str}_{len(existing)}",
    )

    if st.button("💾 Simpan Absensi", type="primary"):
        baru = diperbarui = 0
        gagal = []
        with db() as conn:
            for rec in edited.to_dict("records"):
                nis = str(rec["NIS"])
                status = rec["Status"]
                ket = bersihkan(rec.get("Keterangan")) or None

                if status not in STATUS:
                    gagal.append(nis)
                    continue

                try:
                    if nis in existing:
                        cur = conn.execute(
                            "UPDATE absensi SET status = ?, keterangan = ? "
                            "WHERE nis = ? AND tanggal = ?",
                            (status, ket, nis, tanggal_str),
                        )
                        if cur.rowcount:
                            diperbarui += 1
                    else:
                        conn.execute(
                            "INSERT INTO absensi (nis, tanggal, status, keterangan) "
                            "VALUES (?, ?, ?, ?)",
                            (nis, tanggal_str, status, ket),
                        )
                        baru += 1
                except sqlite3.IntegrityError:
                    # UNIQUE(nis, tanggal) mencegah catatan ganda
                    gagal.append(nis)

        if gagal:
            flash(
                f"{baru} catatan baru dan {diperbarui} catatan diperbarui. "
                f"{len(gagal)} data ditolak karena duplikasi/tidak valid.",
                "warning",
            )
        else:
            flash(
                f"Absensi {pilihan_kelas} tanggal {tanggal_str} tersimpan "
                f"({baru} baru, {diperbarui} diperbarui)."
            )
        st.rerun()


# ---------------- Halaman: Riwayat ----------------
def halaman_riwayat():
    st.title("📋 Riwayat Absensi")
    st.caption("Cari riwayat berdasarkan kelas, rentang tanggal, NIS, atau nama siswa.")

    kelas_list = daftar_kelas()
    opsi = {"Semua Kelas": None}
    opsi.update(opsi_kelas(kelas_list))

    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        pilihan_kelas = st.selectbox("Kelas", list(opsi.keys()), key="riwayat_kelas")
    with c2:
        mulai = st.date_input(
            "Dari tanggal", value=date.today().replace(day=1), key="riwayat_mulai"
        )
    with c3:
        sampai = st.date_input("Sampai tanggal", value=date.today(), key="riwayat_sampai")

    cari = st.text_input(
        "Cari NIS atau nama siswa", placeholder="Contoh: 1001 atau Bunga", key="riwayat_cari"
    ).strip()

    if mulai > sampai:
        st.error("Tanggal awal tidak boleh melebihi tanggal akhir.")
        return

    sql = """
        SELECT a.id_absensi, a.tanggal, s.nis, s.nama_siswa, k.nama_kelas,
               a.status, COALESCE(a.keterangan, '') AS keterangan
        FROM absensi a
        JOIN siswa s ON s.nis = a.nis
        JOIN kelas k ON k.id_kelas = s.id_kelas
        WHERE a.tanggal BETWEEN ? AND ?
    """
    params = [mulai.isoformat(), sampai.isoformat()]

    if opsi[pilihan_kelas] is not None:
        sql += " AND s.id_kelas = ?"
        params.append(opsi[pilihan_kelas])
    if cari:
        sql += " AND (s.nis LIKE ? OR s.nama_siswa LIKE ?)"
        params.extend([f"%{cari}%", f"%{cari}%"])

    sql += " ORDER BY a.tanggal DESC, k.nama_kelas, s.nama_siswa"
    data = q(sql, tuple(params))

    if not data:
        st.info("Data kosong. Belum ada riwayat absensi untuk filter yang dipilih.")
        return

    st.caption(f"{len(data)} catatan ditemukan.")
    tabel = pd.DataFrame(data).drop(columns=["id_absensi"])
    tabel = tabel.rename(
        columns={
            "tanggal": "Tanggal",
            "nis": "NIS",
            "nama_siswa": "Nama Siswa",
            "nama_kelas": "Kelas",
            "status": "Status",
            "keterangan": "Keterangan",
        }
    )
    st.dataframe(tabel, hide_index=True, width="stretch")

    with st.expander("🗑️ Hapus catatan absensi"):
        pilihan = {
            f"{r['tanggal']} · {r['nama_siswa']} ({r['nama_kelas']}) · {r['status']}": r[
                "id_absensi"
            ]
            for r in data
        }
        dipilih = st.selectbox("Pilih catatan", list(pilihan.keys()), key="hapus_absensi_pilih")
        konfirmasi = st.checkbox(
            "Saya yakin ingin menghapus catatan ini.", key="hapus_absensi_konfirmasi"
        )
        if st.button("Hapus Catatan", disabled=not konfirmasi):
            run("DELETE FROM absensi WHERE id_absensi = ?", (pilihan[dipilih],))
            flash("Catatan absensi berhasil dihapus.")
            st.rerun()


# ---------------- Halaman: Rekap ----------------
def halaman_rekap():
    st.title("📊 Rekap Absensi")
    kelas_list = daftar_kelas()
    if not kelas_list:
        st.warning("Belum ada data kelas. Tambahkan kelas terlebih dahulu.")
        return

    opsi = opsi_kelas(kelas_list)
    tab_harian, tab_bulanan = st.tabs(["Rekap Harian", "Laporan Bulanan"])

    # --- Harian ---
    with tab_harian:
        c1, c2 = st.columns(2)
        with c1:
            pilihan_kelas = st.selectbox("Kelas", list(opsi.keys()), key="rekap_h_kelas")
        with c2:
            tanggal = st.date_input("Tanggal", value=date.today(), key="rekap_h_tanggal")

        id_kelas = opsi[pilihan_kelas]
        data = q(
            """
            SELECT s.nis, s.nama_siswa, COALESCE(a.status, 'Belum dicatat') AS status,
                   COALESCE(a.keterangan, '') AS keterangan
            FROM siswa s
            LEFT JOIN absensi a ON a.nis = s.nis AND a.tanggal = ?
            WHERE s.id_kelas = ?
            ORDER BY s.nama_siswa
            """,
            (tanggal.isoformat(), id_kelas),
        )

        if not data:
            st.info("Belum ada siswa di kelas ini.")
            return

        jumlah = {s: sum(1 for r in data if r["status"] == s) for s in STATUS}
        belum = sum(1 for r in data if r["status"] == "Belum dicatat")

        st.caption(
            f"Tanggal {tanggal.isoformat()} · {pilihan_kelas} · "
            f"{len(data)} siswa · {len(data) - belum} sudah tercatat"
        )
        kolom = st.columns(5)
        for col, status in zip(kolom, STATUS):
            col.metric(status, jumlah[status])

        if belum:
            st.warning(f"{belum} siswa belum dicatat pada tanggal ini.")

        tabel = pd.DataFrame(data).rename(
            columns={
                "nis": "NIS",
                "nama_siswa": "Nama Siswa",
                "status": "Status",
                "keterangan": "Keterangan",
            }
        )
        st.dataframe(tabel, hide_index=True, width="stretch")

    # --- Bulanan ---
    with tab_bulanan:
        today = date.today()
        c1, c2, c3 = st.columns(3)
        with c1:
            pilihan_kelas = st.selectbox("Kelas", list(opsi.keys()), key="rekap_b_kelas")
        with c2:
            bulan_label = st.selectbox(
                "Bulan", BULAN, index=today.month - 1, key="rekap_b_bulan"
            )
        with c3:
            tahun = st.selectbox(
                "Tahun",
                list(range(today.year + 1, today.year - 3, -1)),
                index=1,
                key="rekap_b_tahun",
            )

        bulan = BULAN.index(bulan_label) + 1
        periode = f"{tahun}-{bulan:02d}"
        id_kelas = opsi[pilihan_kelas]

        data = q(
            """
            SELECT s.nis, s.nama_siswa,
                   COUNT(a.id_absensi) AS total,
                   SUM(CASE WHEN a.status = 'Hadir'     THEN 1 ELSE 0 END) AS hadir,
                   SUM(CASE WHEN a.status = 'Sakit'     THEN 1 ELSE 0 END) AS sakit,
                   SUM(CASE WHEN a.status = 'Izin'      THEN 1 ELSE 0 END) AS izin,
                   SUM(CASE WHEN a.status = 'Alpa'      THEN 1 ELSE 0 END) AS alpa,
                   SUM(CASE WHEN a.status = 'Terlambat' THEN 1 ELSE 0 END) AS terlambat
            FROM siswa s
            LEFT JOIN absensi a
                   ON a.nis = s.nis AND substr(a.tanggal, 1, 7) = ?
            WHERE s.id_kelas = ?
            GROUP BY s.nis, s.nama_siswa
            ORDER BY s.nama_siswa
            """,
            (periode, id_kelas),
        )

        st.caption(f"Periode {bulan_label} {tahun} · {pilihan_kelas}")
        total = {s: sum(int(r[s.lower()]) for r in data) for s in STATUS}
        kolom = st.columns(5)
        for col, status in zip(kolom, STATUS):
            col.metric(status, total[status])

        if not any(r["total"] for r in data):
            st.info("Data kosong. Belum ada absensi pada periode ini.")
        else:
            tabel = pd.DataFrame(data).rename(
                columns={
                    "nis": "NIS",
                    "nama_siswa": "Nama Siswa",
                    "total": "Total Tercatat",
                    "hadir": "Hadir",
                    "sakit": "Sakit",
                    "izin": "Izin",
                    "alpa": "Alpa",
                    "terlambat": "Terlambat",
                }
            )
            st.dataframe(tabel, hide_index=True, width="stretch")

            grafik = pd.DataFrame(
                {"Jumlah": [total[s] for s in STATUS]}, index=STATUS
            )
            st.bar_chart(grafik, y="Jumlah")


# ---------------- Halaman: Data Siswa ----------------
def halaman_siswa():
    st.title("👨‍🎓 Data Siswa")
    kelas_list = daftar_kelas()
    opsi = opsi_kelas(kelas_list)

    tab_tambah, tab_ubah, tab_daftar = st.tabs(["Tambah Siswa", "Ubah / Hapus", "Daftar Siswa"])

    with tab_tambah:
        if not kelas_list:
            st.warning("Tambahkan data kelas terlebih dahulu.")
        else:
            with st.form("form_tambah_siswa", clear_on_submit=True):
                nis = st.text_input("NIS *", placeholder="Contoh: 1025")
                nama = st.text_input("Nama Siswa *")
                jk = st.selectbox(
                    "Jenis Kelamin",
                    ["L", "P"],
                    format_func=lambda x: "Laki-laki" if x == "L" else "Perempuan",
                )
                kelas = st.selectbox("Kelas *", list(opsi.keys()))
                simpan = st.form_submit_button("Simpan Siswa")

            if simpan:
                if not nis.strip() or not nama.strip():
                    st.error("NIS dan nama siswa wajib diisi.")
                else:
                    try:
                        run(
                            "INSERT INTO siswa (nis, nama_siswa, jenis_kelamin, id_kelas) "
                            "VALUES (?, ?, ?, ?)",
                            (nis.strip(), nama.strip(), jk, opsi[kelas]),
                        )
                        flash(f"Siswa {nama.strip()} berhasil ditambahkan.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("NIS sudah digunakan siswa lain. NIS harus unik.")

    with tab_ubah:
        semua = q(
            """
            SELECT s.nis, s.nama_siswa, s.jenis_kelamin, s.id_kelas,
                   k.nama_kelas, k.tingkat
            FROM siswa s JOIN kelas k ON k.id_kelas = s.id_kelas
            ORDER BY k.nama_kelas, s.nama_siswa
            """
        )
        if not semua:
            st.info("Belum ada data siswa.")
        else:
            pilihan = {
                f"{r['nis']} · {r['nama_siswa']} ({r['nama_kelas']})": r for r in semua
            }
            dipilih = st.selectbox("Pilih siswa", list(pilihan.keys()), key="ubah_siswa_pilih")
            siswa = pilihan[dipilih]

            with st.form("form_ubah_siswa"):
                st.text_input("NIS", value=siswa["nis"], disabled=True)
                nama = st.text_input("Nama Siswa *", value=siswa["nama_siswa"])
                jk = st.selectbox(
                    "Jenis Kelamin",
                    ["L", "P"],
                    index=0 if siswa["jenis_kelamin"] == "L" else 1,
                    format_func=lambda x: "Laki-laki" if x == "L" else "Perempuan",
                )
                labels = list(opsi.keys())
                current = f"{siswa['nama_kelas']} (Tingkat {siswa['tingkat']})"
                kelas = st.selectbox(
                    "Kelas *", labels, index=labels.index(current) if current in labels else 0
                )
                simpan = st.form_submit_button("Simpan Perubahan")

            if simpan:
                if not nama.strip():
                    st.error("Nama siswa wajib diisi.")
                else:
                    run(
                        "UPDATE siswa SET nama_siswa = ?, jenis_kelamin = ?, id_kelas = ? "
                        "WHERE nis = ?",
                        (nama.strip(), jk, opsi[kelas], siswa["nis"]),
                    )
                    flash("Data siswa berhasil diperbarui.")
                    st.rerun()

            st.divider()
            jumlah = q(
                "SELECT COUNT(*) AS c FROM absensi WHERE nis = ?", (siswa["nis"],)
            )[0]["c"]
            st.caption(f"Siswa ini memiliki {jumlah} catatan absensi.")

            konfirmasi = st.checkbox(
                "Saya yakin ingin menghapus siswa ini.",
                key=f"konfirmasi_hapus_{siswa['nis']}",
            )
            if st.button("Hapus Siswa", disabled=not konfirmasi):
                if jumlah:
                    st.error(
                        "Siswa tidak dapat dihapus karena masih memiliki riwayat absensi."
                    )
                else:
                    run("DELETE FROM siswa WHERE nis = ?", (siswa["nis"],))
                    flash("Data siswa berhasil dihapus.")
                    st.rerun()

    with tab_daftar:
        data = q(
            """
            SELECT s.nis, s.nama_siswa,
                   CASE s.jenis_kelamin WHEN 'L' THEN 'Laki-laki' ELSE 'Perempuan' END
                       AS jenis_kelamin,
                   k.nama_kelas, k.tingkat
            FROM siswa s JOIN kelas k ON k.id_kelas = s.id_kelas
            ORDER BY k.nama_kelas, s.nama_siswa
            """
        )
        if not data:
            st.info("Belum ada data siswa.")
        else:
            st.caption(f"Total {len(data)} siswa.")
            tabel = pd.DataFrame(data).rename(
                columns={
                    "nis": "NIS",
                    "nama_siswa": "Nama Siswa",
                    "jenis_kelamin": "Jenis Kelamin",
                    "nama_kelas": "Kelas",
                    "tingkat": "Tingkat",
                }
            )
            st.dataframe(tabel, hide_index=True, width="stretch")


# ---------------- Halaman: Data Kelas ----------------
def halaman_kelas():
    st.title("🏫 Data Kelas")
    tab_tambah, tab_daftar = st.tabs(["Tambah Kelas", "Daftar / Hapus Kelas"])

    with tab_tambah:
        with st.form("form_tambah_kelas", clear_on_submit=True):
            nama = st.text_input("Nama Kelas *", placeholder="Contoh: XII-1")
            tingkat = st.selectbox("Tingkat *", ["X", "XI", "XII"])
            simpan = st.form_submit_button("Simpan Kelas")
        if simpan:
            if not nama.strip():
                st.error("Nama kelas wajib diisi.")
            else:
                try:
                    run(
                        "INSERT INTO kelas (nama_kelas, tingkat) VALUES (?, ?)",
                        (nama.strip(), tingkat),
                    )
                    flash(f"Kelas {nama.strip()} berhasil ditambahkan.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Nama kelas sudah terdaftar. Gunakan nama lain.")

    with tab_daftar:
        data = q(
            """
            SELECT k.id_kelas, k.nama_kelas, k.tingkat, COUNT(s.nis) AS jumlah_siswa
            FROM kelas k
            LEFT JOIN siswa s ON s.id_kelas = k.id_kelas
            GROUP BY k.id_kelas, k.nama_kelas, k.tingkat
            ORDER BY k.tingkat, k.nama_kelas
            """
        )
        if not data:
            st.info("Belum ada data kelas.")
        else:
            tabel = pd.DataFrame(data).drop(columns=["id_kelas"]).rename(
                columns={
                    "nama_kelas": "Nama Kelas",
                    "tingkat": "Tingkat",
                    "jumlah_siswa": "Jumlah Siswa",
                }
            )
            st.dataframe(tabel, hide_index=True, width="stretch")

            st.divider()
            pilihan = {
                f"{r['nama_kelas']} (Tingkat {r['tingkat']})": r for r in data
            }
            dipilih = st.selectbox("Pilih kelas", list(pilihan.keys()), key="hapus_kelas_pilih")
            kelas = pilihan[dipilih]
            st.caption(f"Kelas ini memiliki {kelas['jumlah_siswa']} siswa.")

            konfirmasi = st.checkbox(
                "Saya yakin ingin menghapus kelas ini.",
                key=f"konfirmasi_hapus_kelas_{kelas['id_kelas']}",
            )
            if st.button("Hapus Kelas", disabled=not konfirmasi):
                if kelas["jumlah_siswa"]:
                    st.error(
                        "Kelas tidak dapat dihapus karena masih memiliki siswa. "
                        "Pindahkan atau hapus siswanya terlebih dahulu."
                    )
                else:
                    run("DELETE FROM kelas WHERE id_kelas = ?", (kelas["id_kelas"],))
                    flash("Data kelas berhasil dihapus.")
                    st.rerun()


# ---------------- Main ----------------
init_db()

with st.sidebar:
    st.header("🏫 Absensi Siswa")
    st.caption("SMA Cendekia · Kelompok 6")
    menu = st.radio(
        "Menu",
        ["📝 Absensi", "📋 Riwayat", "📊 Rekap", "👨‍🎓 Data Siswa", "🏫 Data Kelas"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Data contoh dibuat otomatis saat aplikasi pertama dijalankan.")
    st.caption(f"Database: `{DB_PATH}`")

tampilkan_flash()

if menu == "📝 Absensi":
    halaman_absensi()
elif menu == "📋 Riwayat":
    halaman_riwayat()
elif menu == "📊 Rekap":
    halaman_rekap()
elif menu == "👨‍🎓 Data Siswa":
    halaman_siswa()
else:
    halaman_kelas()
