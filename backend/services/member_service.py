from backend.repositories import member_repository as repo


def list_members():
    members = repo.list_members()
    members.sort(key=lambda m: (not m.get("active"), m.get("name") or ""))
    return members


def register_member(phone: str, name: str, registered_by: str):
    if not phone or not phone.strip():
        raise ValueError("Nomor WA wajib diisi.")
    return repo.register_member(phone.strip(), (name or "").strip(), registered_by)


def set_active(phone: str, active: bool):
    result = repo.set_active(phone, active)
    if result is None:
        raise ValueError("Anggota tidak ditemukan.")
    return result


def delete_member(phone: str):
    if not repo.delete_member(phone):
        raise ValueError("Anggota tidak ditemukan.")
    return True


def is_member_allowed(jid_or_phone: str) -> bool:
    return repo.is_member_active(jid_or_phone)
