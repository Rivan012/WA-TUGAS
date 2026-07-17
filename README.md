# WA Tugas Bot

Bot WhatsApp untuk mencatat tugas kuliah, dengan reminder otomatis mendekati deadline. Ditulis dengan Python (FastAPI) sebagai backend, Node.js (Baileys) sebagai gateway WhatsApp, dan Firestore sebagai database. Ada juga dashboard web untuk mengelola grup WhatsApp mana saja yang boleh dibalas bot.

## Fitur

- Tambah tugas via WhatsApp, mendukung format bebas (diparse otomatis pakai Google Gemini) maupun format kaku `key: value`
- Reminder otomatis 3 tahap: **H-3**, **H-1** (dikirim jam 00:00, 12:00, dan 22:00 setiap hari), dan **H-1 Jam** (dicek tiap 5 menit biar presisi)
- List, tandai selesai, dan hapus tugas
- Validasi deadline tidak boleh di masa lalu
- **Dukungan grup WhatsApp**: bot hanya membalas di grup yang didaftarkan lewat dashboard, dan hanya kalau anggota grup nge-*tag*/mention bot bersama perintahnya
- **Dashboard web** (login diperlukan) untuk mengaktifkan/menonaktifkan/menghapus grup terdaftar

## Arsitektur

```
WhatsApp User / Grup
     │
     ▼
whatsapp/index.js  (Node.js + Baileys)
  - Terima pesan masuk, deteksi grup vs pribadi & mention/tag bot
  - Lapor grup baru ke backend (POST /webhook/group-seen)
  - Teruskan pesan yang lolos filter ke backend
  - Expose endpoint POST /send-message untuk kirim WA dari backend
     │  HTTP
     ▼
backend/routes/webhook.py  (FastAPI)
  - Filter: grup harus terdaftar+aktif, dan pesan harus nge-tag bot
     │
     ▼
backend/commands/*.py  (tambah, list, selesai, hapus, help)
     │
     ▼
backend/services/*.py  →  Firestore (backend/firebase_service.py)

backend/scheduler.py (APScheduler)
     │
     ├─ Cron 00:00 / 12:00 / 22:00 → reminder H-3 & H-1
     └─ Interval tiap 5 menit      → reminder H-1 Jam
     ▼
backend/jobs/reminder_job.py  →  cek deadline  →  kirim reminder via gateway WA

Dashboard Web (frontend/, statis)
     │  HTTP + cookie session
     ▼
backend/routes/auth.py    → login/logout (JWT di cookie httpOnly)
backend/routes/groups.py  → CRUD grup terdaftar
```

## Struktur Proyek

```
wa-tugas/
├─ .env                        # kredensial & config (lihat bagian Environment Variables)
├─ backend/
│  ├─ app.py                   # entry point FastAPI, mount router + dashboard statis, start scheduler
│  ├─ config.py                # baca env vars
│  ├─ firebase_service.py      # koneksi Firestore
│  ├─ scheduler.py             # setup APScheduler (cron H-3/H-1, interval H-1 Jam)
│  ├─ commands/                # 1 file = 1 command WhatsApp
│  │  ├─ tambah.py
│  │  ├─ list.py
│  │  ├─ selesai.py
│  │  ├─ hapus.py
│  │  └─ help.py
│  ├─ jobs/
│  │  └─ reminder_job.py       # cek deadline & kirim reminder H-3/H-1/H-1 Jam
│  ├─ models/
│  │  └─ task.py               # skema data tugas
│  ├─ repositories/
│  │  ├─ task_repository.py    # akses Firestore untuk task
│  │  ├─ group_repository.py   # akses Firestore untuk grup terdaftar
│  │  └─ user_repository.py    # akses Firestore untuk akun dashboard
│  ├─ routes/
│  │  ├─ webhook.py            # endpoint yang dipanggil gateway WA + group-seen
│  │  ├─ auth.py                # login/logout dashboard
│  │  └─ groups.py              # CRUD grup terdaftar (butuh login)
│  ├─ scripts/
│  │  └─ create_admin.py       # CLI buat akun dashboard pertama kali
│  ├─ services/
│  │  ├─ ai_parser.py          # parsing bahasa bebas via Gemini
│  │  ├─ task.py                # business logic task
│  │  ├─ group_service.py       # business logic grup terdaftar
│  │  ├─ auth_service.py        # hashing password & JWT session
│  │  └─ whatsapp_service.py   # kirim pesan ke gateway WA
│  └─ utils/
│     └─ parser.py             # parsing format kaku key:value
├─ frontend/                   # dashboard web statis (login + kelola grup)
│  ├─ index.html               # halaman login
│  ├─ app.html                 # halaman kelola grup
│  ├─ style.css
│  └─ app.js
├─ credentials/
│  └─ firebase.json            # service account Firestore
└─ whatsapp/
   ├─ index.js                 # Express + Baileys gateway (deteksi grup & tag)
   ├─ auth/                    # sesi WhatsApp tersimpan (jangan di-commit)
   └─ package.json
```

## Persiapan

### 1. Backend (Python)

```bash
cd wa-tugas
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

Dependensi utama: `fastapi`, `uvicorn`, `apscheduler`, `google-cloud-firestore`, `google-genai`, `requests`, `python-dotenv`, `PyJWT`.

### 2. Gateway WhatsApp (Node.js)

```bash
cd whatsapp
npm install
node index.js
```

Scan QR code yang muncul di terminal menggunakan WhatsApp di HP (Linked Devices). Tunggu sampai muncul:
```
✅ WhatsApp Connected
Logged in as: 62xxxxxxxxxx@s.whatsapp.net
```

### 3. Environment Variables (`.env`)

```env
GOOGLE_AI_API_KEY=your_gemini_api_key_here
FIREBASE_CREDENTIALS_PATH=./credentials/firebase.json

# WAJIB diganti untuk production — dipakai menandatangani sesi login dashboard
DASHBOARD_SECRET_KEY=ganti-dengan-string-acak-yang-panjang
DASHBOARD_TOKEN_EXPIRE_HOURS=12

# Zona waktu untuk jadwal reminder H-3/H-1 (default Asia/Jakarta)
TIMEZONE=Asia/Jakarta

# URL backend yang dipanggil gateway WA (default http://127.0.0.1:8000)
BACKEND_URL=http://127.0.0.1:8000
```

Dapatkan Gemini API key dari https://aistudio.google.com/apikey

### 4. Buat akun dashboard pertama kali

Dashboard **tidak punya halaman daftar akun publik** (sengaja, biar tidak sembarang orang bisa bikin akun). Buat akun admin lewat terminal server:

```bash
cd wa-tugas
python -m backend.scripts.create_admin
```

Ikuti prompt untuk isi username & password.

### 5. Jalankan backend

```bash
cd wa-tugas
uvicorn backend.app:app --reload --port 8000
```

Dashboard bisa diakses di `http://127.0.0.1:8000/dashboard/`.

## Cara Pakai (dari WhatsApp)

### Chat pribadi ke bot
Sama seperti biasa, tidak perlu tag:
```
/tambah tugas laporan praktikum fisika deadline besok jam 8 malam
/list
/selesai TSK001
/hapus TSK001
/help
```

### Di dalam grup WhatsApp
1. Tambahkan bot ke grup.
2. Kirim satu pesan apa saja di grup — grup otomatis muncul di dashboard (`/dashboard/`) dalam status **"Menunggu Aktivasi"**.
3. Login ke dashboard, aktifkan grup tersebut (toggle jadi hijau). Atau daftarkan manual lewat form kalau sudah tahu Group JID-nya.
4. Setelah aktif, anggota grup **wajib nge-tag/mention bot** di setiap pesan perintah, contoh:
   ```
   @NamaBot /tambah tugas laporan fisika deadline besok jam 8 malam
   @NamaBot /list
   ```
   Pesan grup yang tidak nge-tag bot, atau dari grup yang belum diaktifkan, akan **diabaikan** (bot tidak membalas apa pun).
5. Tugas yang ditambahkan dari grup tetap tercatat atas nama pengirim aslinya (bukan grupnya), jadi `/list` di grup hanya menampilkan tugas milik orang yang mengirim perintah.

## Reminder Otomatis

`reminder_job.py` dijalankan oleh `scheduler.py` dengan 2 jadwal terpisah:

| Stage | Kapan dicek/dikirim | Field penanda di Firestore |
|---|---|---|
| H-3 | Jam **00:00, 12:00, 22:00** setiap hari (kalau sudah masuk window ≤ 3 hari sebelum deadline) | `reminder_h3` |
| H-1 | Jam **00:00, 12:00, 22:00** setiap hari (kalau sudah masuk window ≤ 1 hari sebelum deadline) | `reminder_h1` |
| H-1 Jam | Dicek tiap **5 menit** (butuh presisi mendekati deadline) | `reminder_1jam` |

Catatan penting:
- Tiap stage hanya terkirim sekali (flag di-set `True` setelah **berhasil** terkirim, bukan sekadar dicoba).
- Task yang deadline-nya sudah lewat lebih dari 15 menit sejak dibuat **tidak** akan mendapat reminder susulan (mencegah task lama/telat input dianggap "H-1 Jam").
- Deadline dengan waktu di masa lalu ditolak sejak awal saat `/tambah`.
- Reminder selalu dikirim sebagai pesan **pribadi** ke pengirim tugas (`user_id`), baik tugas itu ditambahkan dari chat pribadi maupun dari grup.

## Dashboard Web (Kelola Grup)

Dashboard statis di `frontend/`, dilayani otomatis oleh backend di `/dashboard/`.

- **Login** (`/dashboard/index.html`) — pakai akun yang dibuat lewat `python -m backend.scripts.create_admin`. Sesi disimpan di cookie httpOnly (JWT), berlaku sesuai `DASHBOARD_TOKEN_EXPIRE_HOURS`.
- **Kelola Grup** (`/dashboard/app.html`) — lihat semua grup (aktif & menunggu aktivasi), aktifkan/nonaktifkan lewat toggle, daftarkan grup baru manual (Group JID + nama), atau hapus grup dari daftar.

### Endpoint API dashboard
| Method | Endpoint | Keterangan |
|---|---|---|
| POST | `/api/auth/login` | Login, set cookie sesi |
| POST | `/api/auth/logout` | Logout, hapus cookie |
| GET | `/api/auth/me` | Cek sesi aktif |
| GET | `/api/groups` | Daftar semua grup |
| POST | `/api/groups` | Daftarkan/aktifkan grup manual (`{jid, name}`) |
| PATCH | `/api/groups/{jid}/active` | Aktifkan/nonaktifkan grup (`{active: bool}`) |
| DELETE | `/api/groups/{jid}` | Hapus grup dari daftar |

Semua endpoint `/api/groups/*` butuh cookie sesi (login dulu lewat `/api/auth/login`).

## Skema Dokumen Firestore

### Collection `tasks`
```json
{
  "nama": "Laporan Praktikum",
  "matkul": "Fisika",
  "deadline": "2026-07-20T20:00:00",
  "catatan": "kumpul ke asisten lab",
  "status": "belum",
  "user_id": "6281234567890@s.whatsapp.net",
  "reminder_h3": false,
  "reminder_h1": false,
  "reminder_1jam": false
}
```

### Collection `groups`
```json
{
  "jid": "120363012345678901@g.us",
  "name": "Kelas A - Tugas",
  "active": true,
  "registered_by": "rivan",
  "created_at": "2026-07-17T10:00:00",
  "last_seen_at": "2026-07-17T12:30:00"
}
```

### Collection `dashboard_users`
```json
{
  "username": "rivan",
  "password_hash": "...",
  "salt": "...",
  "created_at": "2026-07-17T09:00:00"
}
```

## Troubleshooting

| Gejala | Kemungkinan Penyebab |
|---|---|
| Reminder tidak terkirim sama sekali | Gateway WA (`whatsapp/index.js`) tidak jalan di port 3000, atau `sock.user` belum ter-autentikasi |
| Reminder terkirim berulang-ulang | `send_message()` tidak `return True/False`, sehingga status di Firestore tidak pernah ter-update |
| `Cannot destructure property 'user' of jidDecode(...)` | Sesi WhatsApp corrupt — hapus folder `whatsapp/auth` dan scan ulang QR |
| `/tambah` gagal parse pesan bebas | Cek `GOOGLE_AI_API_KEY` sudah benar dan model belum deprecated (cek [Gemini deprecations](https://ai.google.dev/gemini-api/docs/changelog)) |
| Field `nama` wajib diisi padahal sudah diisi | AI parser gagal (cek log `[tambah] AI parser gagal...`), fallback ke parser manual yang butuh format `key: value` |
| Bot diam saja di grup | Grup belum diaktifkan di dashboard, atau anggota lupa nge-tag/mention bot di pesannya |
| Grup tidak muncul di dashboard | Belum ada pesan terkirim di grup itu sejak bot ditambahkan — kirim 1 pesan apa saja dulu, atau daftarkan manual pakai Group JID |
| `401 Unauthorized` saat akses dashboard | Sesi login sudah kedaluwarsa (`DASHBOARD_TOKEN_EXPIRE_HOURS`) — login ulang |

## Lisensi

Proyek internal / pribadi.
