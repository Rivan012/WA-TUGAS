import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.commands import (
    tambah,
    list,
    selesai,
    hapus,
    help
)
from backend.services.group_service import is_group_allowed, note_group_seen
from backend.services.member_service import is_member_allowed

router = APIRouter()
logger = logging.getLogger("webhook")


class IncomingMessage(BaseModel):
    from_number: str          # identitas pengirim asli (dipakai buat kepemilikan tugas)
    message: str
    chat_id: Optional[str] = None    # jid tujuan balasan (grup atau pribadi)
    is_group: bool = False
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    is_mentioned: bool = False       # True kalau bot di-tag di pesan grup


class GroupSeenMessage(BaseModel):
    group_id: str
    group_name: Optional[str] = None


@router.post("/webhook")
def webhook(data: IncomingMessage):

    text = data.message.strip()

    # --- Filter khusus pesan dari grup ---
    if data.is_group:
        if not data.group_id or not is_group_allowed(data.group_id):
            # Grup belum didaftarkan/diaktifkan lewat dashboard -> bot diam saja
            logger.info("Pesan dari grup belum terdaftar (%s), diabaikan.", data.group_id)
            return {"reply": None}

        if not data.is_mentioned:
            # Anggota grup tidak nge-tag bot -> bot diam saja
            return {"reply": None}

        if not is_member_allowed(data.from_number):
            # Anggota belum diizinkan admin (lihat dashboard > Anggota Diizinkan) -> bot diam saja
            logger.info("Sender %s belum diizinkan, diabaikan.", data.from_number)
            return {"reply": None}

    user_id = data.from_number

    if text.startswith("/tambah"):
        reply = tambah.execute(user_id, text)

    elif text.startswith("/list"):
        reply = list.execute(user_id)

    elif text.startswith("/selesai"):
        reply = selesai.execute(text)

    elif text.startswith("/hapus"):
        reply = hapus.execute(text)

    else:
        reply = help.execute()

    return {"reply": reply}


@router.post("/webhook/group-seen")
def group_seen(data: GroupSeenMessage):
    """
    Dipanggil gateway WA setiap kali bot melihat pesan dari grup yang belum
    dikenal, supaya grup itu otomatis muncul di dashboard (dalam status
    nonaktif) dan tinggal diaktifkan admin.
    """
    note_group_seen(data.group_id, data.group_name)
    return {"success": True}
