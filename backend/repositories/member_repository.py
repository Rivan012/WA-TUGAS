from datetime import datetime
from backend.firebase_service import db

COLLECTION = "allowed_members"


def normalize_phone(phone_or_jid: str) -> str:
    """
    Samain format nomor WA, baik yang diinput admin di dashboard (mis. '6281234567890'
    atau '081234567890' atau '+6281234567890') maupun yang datang dari webhook
    (JID lengkap 'from_number', mis. '6281234567890@s.whatsapp.net' atau ada device-id
    '6281234567890:12@s.whatsapp.net'), supaya bisa dibandingkan apple-to-apple.
    """
    raw = phone_or_jid.split("@")[0].split(":")[0].strip().lstrip("+")
    raw = "".join(ch for ch in raw if ch.isdigit())

    # Nomor lokal yang diketik admin diawali '0' -> ganti ke kode negara 62 (Indonesia)
    if raw.startswith("0"):
        raw = "62" + raw[1:]

    return raw


def _doc(phone):
    return db.collection(COLLECTION).document(normalize_phone(phone))


def get_member(phone):
    snap = _doc(phone).get()
    return snap.to_dict() if snap.exists else None


def is_member_active(phone) -> bool:
    member = get_member(phone)
    return bool(member and member.get("active"))


def list_members():
    docs = db.collection(COLLECTION).stream()
    return [doc.to_dict() for doc in docs]


def register_member(phone, name, registered_by):
    normalized = normalize_phone(phone)
    if not normalized:
        raise ValueError("Nomor WA tidak valid.")

    ref = _doc(normalized)
    snap = ref.get()

    if snap.exists:
        ref.update({
            "name": name or snap.to_dict().get("name", normalized),
            "active": True,
            "registered_by": registered_by,
        })
    else:
        ref.set({
            "phone": normalized,
            "name": name or normalized,
            "active": True,
            "registered_by": registered_by,
            "created_at": datetime.now().isoformat(),
        })

    return _doc(normalized).get().to_dict()


def set_active(phone, active: bool):
    ref = _doc(phone)
    if not ref.get().exists:
        return None
    ref.update({"active": active})
    return ref.get().to_dict()


def delete_member(phone):
    ref = _doc(phone)
    if not ref.get().exists:
        return False
    ref.delete()
    return True
