# 📅 Agenda - Website To Do List Berbasis Kalender & Pengingat

> Aplikasi To Do List berbasis desktop modern yang menggabungkan manajemen tugas dengan kalender interaktif, detail rincian event, dan notifikasi pengingat jatuh tempo.

Dibangun dengan **Python (Flask)**, **SQLAlchemy**, **APScheduler**, **Tailwind CSS**, dan **FullCalendar**.

---

## 🌟 Fitur Utama (MVP v1.0)

1. **Tampilan Kalender 3 Tampilan**:
   - Tampilan Bulan (*Month*), Minggu (*Week*), dan Hari (*Day*).
   - Navigasi periode sebelumnya/berikutnya dan tombol cepat "Hari ini".
   - Klik tanggal pada kalender untuk langsung menambah aktivitas baru.
2. **Detail Rincian Event (3-Panel Desktop Layout)**:
   - Panel kiri: Mini kalender, filter status, filter prioritas, daftar kategori berwarna, dan ringkasan "Hari ini & Mendatang".
   - Panel tengah: Kalender interaktif FullCalendar dengan chip event berwarna sesuai kategori.
   - Panel kanan: Detail rincian event (Waktu WIB, Lokasi, Catatan, Kategori, Prioritas, Pengingat) tanpa berpindah halaman.
3. **Pengelolaan Tugas & Status**:
   - Tambah, Ubah, dan Hapus event dengan modal konfirmasi aman (*anti salah klik*).
   - Tandai event *Selesai* atau aktifkan kembali dalam 1 klik.
4. **Sistem Notifikasi Pengingat**:
   - Penjadwalan pengingat otomatis di server via APScheduler (tiap 60 detik).
   - Polling browser tiap 30 detik untuk mendeteksi pengingat jatuh tempo (*due*).
   - Notifikasi Toast elegan di kanan bawah layar dengan tombol **Tunda 10 menit (Snooze)**, **Lihat detail**, dan **Tutup (Ack)**.
   - Integrasi *Notification API* untuk notifikasi desktop asli.
   - Deteksi pengingat terlewat saat browser dibuka kembali.
5. **Kategori & Personalisasi**:
   - Pengelolaan kategori dengan palet warna Hex kustom di halaman Pengaturan (`/settings`).
   - Fitur pencarian instan (*live search*) berdasarkan judul, lokasi, atau deskripsi.

---

## 🛠️ Struktur Proyek

```text
to-do-list/
├── app/
│   ├── __init__.py           # Application Factory & Seeding Default
│   ├── config.py             # Konfigurasi Dev, Test, Prod
│   ├── extensions.py         # Inisialisasi db, migrate, scheduler
│   ├── models.py             # Model User, Category, Event, Reminder
│   ├── schemas.py            # Validasi & Serialisasi Marshmallow
│   ├── scheduler.py          # Background Job APScheduler
│   ├── services/
│   │   ├── event_service.py     # Logika bisnis & query Event
│   │   └── reminder_service.py  # Logika bisnis pengingat & snooze
│   ├── blueprints/
│   │   ├── api.py            # REST API JSON Endpoints
│   │   └── pages.py          # Route Halaman Web Jinja2
│   ├── templates/
│   │   ├── base.html         # Layout utama + Topbar + Toast container
│   │   ├── dashboard.html    # Layout 3 panel + modal dialog
│   │   ├── events_form.html  # Halaman form event mandiri
│   │   ├── events_detail.html# Halaman rincian event mandiri
│   │   └── settings.html     # Pengaturan kategori & perizinan notifikasi
│   └── static/
│       ├── dist/app.css      # CSS kustom & styling FullCalendar
│       └── js/
│           ├── calendar.js   # Interaksi FullCalendar & Panel Detail
│           └── notifications.js # Polling pengingat, Toast & Desktop Notif
├── tests/
│   ├── conftest.py           # Fixture pytest & database in-memory
│   ├── test_api.py           # Pengujian endpoint REST API
│   └── test_critical_scenarios.py # Pengujian skenario kritis T-01 s/d T-08
├── backup.py                 # Skrip pencadangan & pemulihan database
├── server_production.py      # Runner server produksi Waitress
├── requirements.txt          # Daftar dependensi pustaka Python
├── run.py                    # Runner mode pengembangan (Flask dev)
└── README.md
```

---

## 🚀 Panduan Instalasi & Menjalankan

### 1. Prasyarat
- Python 3.12+ (atau Python 3.9+)
- Browser modern (Google Chrome, Microsoft Edge, atau Mozilla Firefox)

### 2. Aktivasi Virtual Environment
```bash
# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

*(Jika membuat venv baru dari nol:)*
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Menjalankan Aplikasi (Mode Pengembangan)
```bash
python run.py
```
Akses di browser: **[http://localhost:5000](http://localhost:5000)**

### 4. Menjalankan Server Produksi (Waitress)
Sesuai rekomendasi dokumen bab 3.1 untuk sistem operasi Windows:
```bash
python server_production.py
```

---

## 🧪 Menjalankan Pengujian Otomatis (Pytest)

Semua skenario uji kritis (T-01 sampai T-08) dan endpoint API diuji secara otomatis:
```bash
pytest -v
```

### Hasil Skenario Uji Kritis:
- **T-01**: Menambah event valid -> Tersimpan & tampil di kalender (**PASSED**)
- **T-02**: Waktu selesai sebelum mulai -> Ditolak dengan pesan kesalahan (**PASSED**)
- **T-03**: Hapus event -> Pengingat otomatis terhapus / cascade (**PASSED**)
- **T-04**: Waktu pengingat tiba -> Status due & notifikasi aktif (**PASSED**)
- **T-05**: Tunda (snooze) 10 menit -> Reminder baru dijadwalkan (**PASSED**)
- **T-06**: Pengingat saat browser tutup -> Tampil terlewat saat buka (**PASSED**)
- **T-07**: Event melewati tengah malam -> Tampil di kedua hari (**PASSED**)
- **T-08**: Reschedule jam mulai -> Remind_at dihitung ulang otomatis (**PASSED**)

---

## 💾 Pencadangan & Pemulihan Database

Aplikasi menyertakan skrip `backup.py` untuk menjaga keandalan data (Bab 2.2):

```bash
# Membuat cadangan database
python backup.py backup

# Memulihkan dari file cadangan
python backup.py restore backups/todo_backup_YYYYMMDD_HHMMSS.db
```

---

## 📋 Endpoint REST API

| Metode | Endpoint | Deskripsi |
|---|---|---|
| `GET` | `/api/events` | Filter rentang tanggal, status, kategori, dan query pencarian |
| `POST` | `/api/events` | Membuat event baru dan jadwal pengingat |
| `GET` | `/api/events/<id>` | Mengambil detail 1 event |
| `PUT` | `/api/events/<id>` | Memperbarui event & menghitung ulang jadwal pengingat |
| `DELETE` | `/api/events/<id>` | Menghapus event beserta pengingatnya (*cascade*) |
| `PATCH` | `/api/events/<id>/status` | Mengubah status (*aktif* / *selesai* / *dibatalkan*) |
| `GET` | `/api/categories` | Mendapatkan daftar kategori |
| `POST` | `/api/categories` | Menambah kategori baru beserta kode warna Hex |
| `PUT` | `/api/categories/<id>` | Mengubah nama atau warna kategori |
| `DELETE`| `/api/categories/<id>` | Menghapus kategori (event menjadi *Tanpa Kategori*) |
| `GET` | `/api/reminders/due` | Mengambil pengingat yang jatuh tempo |
| `POST` | `/api/reminders/<id>/ack` | Menandai pengingat sudah disampaikan (*delivered*) |
| `POST` | `/api/reminders/<id>/snooze` | Menunda pengingat selama N menit |
