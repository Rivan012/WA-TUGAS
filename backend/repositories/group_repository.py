from datetime import datetime
from backend.firebase_service import db

COLLECTION = "groups"


def _doc(jid):
    return db.collection(COLLECTION).document(jid)


def get_group(jid):
    snap = _doc(jid).get()
    return snap.to_dict() if snap.exists else None


def is_group_active(jid):
    group = get_group(jid)
    return bool(group and group.get("active"))


def list_groups():
    docs = db.collection(COLLECTION).stream()
    return [doc.to_dict() for doc in docs]


def upsert_seen_group(jid, name):
    """
    Dipanggil gateway WA setiap kali bot menerima pesan dari grup.
    Kalau grup belum pernah tercatat, dibuat sebagai draft (active=False)
    supaya muncul di dashboard untuk diaktifkan admin.
    Kalau sudah ada, cuma update nama & last_seen (tidak mengubah status active).
    """
    ref = _doc(jid)
    snap = ref.get()

    if not snap.exists:
        ref.set({
            "jid": jid,
            "name": name or jid,
            "active": False,
            "registered_by": None,
            "created_at": datetime.now().isoformat(),
            "last_seen_at": datetime.now().isoformat(),
        })
    else:
        ref.update({
            "name": name or snap.to_dict().get("name", jid),
            "last_seen_at": datetime.now().isoformat(),
        })


def register_group(jid, name, registered_by):
    """Daftarkan/aktifkan grup lewat dashboard (bisa grup baru atau yang sudah 'seen')."""
    ref = _doc(jid)
    snap = ref.get()

    if snap.exists:
        ref.update({
            "name": name or snap.to_dict().get("name", jid),
            "active": True,
            "registered_by": registered_by,
        })
    else:
        ref.set({
            "jid": jid,
            "name": name or jid,
            "active": True,
            "registered_by": registered_by,
            "created_at": datetime.now().isoformat(),
            "last_seen_at": None,
        })

    return _doc(jid).get().to_dict()


def set_active(jid, active: bool):
    ref = _doc(jid)
    if not ref.get().exists:
        return None
    ref.update({"active": active})
    return ref.get().to_dict()


def delete_group(jid):
    ref = _doc(jid)
    if not ref.get().exists:
        return False
    ref.delete()
    return True
