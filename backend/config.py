from dotenv import load_dotenv
import os

load_dotenv()

PORT = int(os.getenv("PORT", 8000))
FIREBASE_CREDENTIAL = os.getenv("FIREBASE_CREDENTIAL")
GOOGLE_AI_API_KEY = os.environ.get("GOOGLE_AI_API_KEY")

# --- Dashboard / Auth ---
# WAJIB diganti di .env untuk production. Dipakai untuk menandatangani token
# login dashboard (JWT). Kalau tidak diset, dashboard tidak akan aman.
DASHBOARD_SECRET_KEY = os.getenv("DASHBOARD_SECRET_KEY", "ubah-secret-ini-di-.env")
DASHBOARD_TOKEN_EXPIRE_HOURS = int(os.getenv("DASHBOARD_TOKEN_EXPIRE_HOURS", 12))

# Zona waktu untuk jadwal notifikasi (lihat backend/scheduler.py)
TIMEZONE = os.getenv("TIMEZONE", "Asia/Jakarta")
