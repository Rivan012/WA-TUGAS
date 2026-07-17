import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Cookie, HTTPException, status

from backend.config import DASHBOARD_SECRET_KEY, DASHBOARD_TOKEN_EXPIRE_HOURS
from backend.repositories.user_repository import create_user, get_user

PBKDF2_ITERATIONS = 200_000
COOKIE_NAME = "wa_tugas_session"


def _hash_password(password: str, salt: str) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS
    )
    return dk.hex()


def register_admin(username: str, password: str):
    """Bikin akun dashboard baru. Dipakai lewat script setup (backend/scripts/create_admin.py)."""
    salt = secrets.token_hex(16)
    password_hash = _hash_password(password, salt)
    created = create_user(username, password_hash, salt)
    if created is None:
        raise ValueError(f"User '{username}' sudah ada.")
    return created


def verify_login(username: str, password: str) -> bool:
    user = get_user(username)
    if not user:
        return False

    expected = user.get("password_hash", "")
    actual = _hash_password(password, user.get("salt", ""))
    return hmac.compare_digest(expected, actual)


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=DASHBOARD_TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, DASHBOARD_SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, DASHBOARD_SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi tidak valid atau sudah kedaluwarsa, silakan login lagi.",
        )


def get_current_user(wa_tugas_session: str | None = Cookie(default=None)):
    """Dependency FastAPI: wajib login (cookie session) untuk akses endpoint dashboard."""
    if not wa_tugas_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Belum login.",
        )
    return decode_access_token(wa_tugas_session)
