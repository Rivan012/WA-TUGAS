# WA Tugas Bot

Bot WhatsApp untuk mencatat tugas kuliah, dengan reminder otomatis mendekati deadline. Ditulis dengan Python (FastAPI) sebagai backend, Node.js (Baileys) sebagai gateway WhatsApp, dan Firestore sebagai database.

## Fitur

- Tambah tugas via WhatsApp, mendukung format bebas (diparse otomatis pakai Google Gemini) maupun format kaku `key: value`
- Reminder otomatis 3 tahap: **H-3**, **H-1**, dan **H-1 Jam** sebelum deadline
- List, tandai selesai, dan hapus tugas
- Validasi deadline tidak boleh di masa lalu

## Arsitektur

```
WhatsApp User
     │
     ▼
whatsapp/index.js  (Node.js + Baileys)
  - Terima pesan masuk, teruskan ke backend
  - Expose endpoint POST /send-message untuk kirim WA dari backend
     │  HTTP
     ▼
backend/routes/webhook.py  (FastAPI)
     │
     ▼
backend/commands/*.py  (tambah, list, selesai, hapus, help)
     │
     ▼
backend/services/*.py  →  Firestore (backend/firebase_service.py)

backend/scheduler.py (APScheduler, jalan tiap 10 detik)
     │
     ▼
backend/jobs/reminder_job.py  →  cek deadline  →  kirim reminder via gateway WA
```

## Struktur Proyek

```
wa-tugas/
├─ .env                        # kredensial & config (lihat bagian Environment Variables)
├─ backend/
│  ├─ app.py                   # entry point FastAPI, start scheduler saat lifespan
│  ├─ config.py                # baca env vars
│  ├─ firebase_service.py      # koneksi Firestore
│  ├─ scheduler.py             # setup APScheduler
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
│  │  └─ task_repository.py    # akses Firestore untuk task
│  ├─ routes/
│  │  └─ webhook.py            # endpoint yang dipanggil gateway WA
│  ├─ services/
│  │  ├─ ai_parser.py          # parsing bahasa bebas via Gemini
│  │  ├─ task.py                # business logic task
│  │  └─ whatsapp_service.py   # kirim pesan ke gateway WA
│  └─ utils/
│     └─ parser.py             # parsing format kaku key:value
├─ credentials/
│  └─ firebase.json            # service account Firestore
└─ whatsapp/
   ├─ index.js                 # Express + Baileys gateway
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

Dependensi utama: `fastapi`, `uvicorn`, `apscheduler`, `google-cloud-firestore`, `google-genai`, `requests`, `python-dotenv`.

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
```

Dapatkan Gemini API key dari https://aistudio.google.com/apikey

### 4. Jalankan backend

```bash
cd wa-tugas
uvicorn backend.app:app --reload --port 8000
```

## Cara Pakai (dari WhatsApp)

### Tambah tugas — format bebas
```
/tambah tugas laporan praktikum fisika deadline besok jam 8 malam
```

### Tambah tugas — format kaku
```
/tambah
nama: Laporan Praktikum
matkul: Fisika
deadline: 2026-07-20T20:00:00
catatan: kumpul ke asisten lab
```

### Command lain
```
/list           - lihat semua tugas aktif
/selesai <id>   - tandai tugas selesai
/hapus <id>     - hapus tugas
/help           - bantuan
```

## Reminder Otomatis

`reminder_job.py` berjalan tiap 10 detik (lihat `scheduler.py`), mengecek semua tugas dengan `status: "belum"`, dan mengirim reminder di 3 tahap:

| Stage | Waktu kirim | Field penanda di Firestore |
|---|---|---|
| H-3 | ≤ 3 hari sebelum deadline | `reminder_h3` |
| H-1 | ≤ 1 hari sebelum deadline | `reminder_h1` |
| H-1 Jam | ≤ 1 jam sebelum deadline | `reminder_1jam` |

Catatan penting:
- Tiap stage hanya terkirim sekali (flag di-set `True` setelah **berhasil** terkirim, bukan sekadar dicoba).
- Task yang deadline-nya sudah lewat lebih dari 15 menit sejak dibuat **tidak** akan mendapat reminder susulan (mencegah task lama/telat input dianggap "H-1 Jam").
- Deadline dengan waktu di masa lalu ditolak sejak awal saat `/tambah`.

## Skema Dokumen `tasks` di Firestore

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

## Troubleshooting

| Gejala | Kemungkinan Penyebab |
|---|---|
| Reminder tidak terkirim sama sekali | Gateway WA (`whatsapp/index.js`) tidak jalan di port 3000, atau `sock.user` belum ter-autentikasi |
| Reminder terkirim berulang-ulang | `send_message()` tidak `return True/False`, sehingga status di Firestore tidak pernah ter-update |
| `Cannot destructure property 'user' of jidDecode(...)` | Sesi WhatsApp corrupt — hapus folder `whatsapp/auth` dan scan ulang QR |
| `/tambah` gagal parse pesan bebas | Cek `GOOGLE_AI_API_KEY` sudah benar dan model belum deprecated (cek [Gemini deprecations](https://ai.google.dev/gemini-api/docs/changelog)) |
| Field `nama` wajib diisi padahal sudah diisi | AI parser gagal (cek log `[tambah] AI parser gagal...`), fallback ke parser manual yang butuh format `key: value` |

## Lisensi

Proyek internal / pribadi.