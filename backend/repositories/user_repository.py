from datetime import datetime
from backend.firebase_service import db

COLLECTION = "dashboard_users"


def get_user(username):
    snap = db.collection(COLLECTION).document(username).get()
    return snap.to_dict() if snap.exists else None


def create_user(username, password_hash, salt):
    ref = db.collection(COLLECTION).document(username)

    if ref.get().exists:
        return None

    data = {
        "username": username,
        "password_hash": password_hash,
        "salt": salt,
        "created_at": datetime.now().isoformat(),
    }
    ref.set(data)
    return data


def user_exists_any():
    """True kalau sudah ada minimal 1 akun dashboard (dipakai buat cek setup awal)."""
    docs = db.collection(COLLECTION).limit(1).stream()
    return len(list(docs)) > 0
