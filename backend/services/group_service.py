from backend.repositories import group_repository as repo


def list_groups():
    groups = repo.list_groups()
    # Grup aktif dulu, lalu yang paling baru dilihat
    groups.sort(key=lambda g: (not g.get("active"), g.get("last_seen_at") or ""), reverse=False)
    return groups


def register_group(jid: str, name: str, registered_by: str):
    jid = jid.strip()
    if not jid.endswith("@g.us"):
        raise ValueError("Format Group JID tidak valid, harus diakhiri '@g.us'.")
    return repo.register_group(jid, name.strip() if name else jid, registered_by)


def set_active(jid: str, active: bool):
    result = repo.set_active(jid, active)
    if result is None:
        raise ValueError("Grup tidak ditemukan.")
    return result


def delete_group(jid: str):
    if not repo.delete_group(jid):
        raise ValueError("Grup tidak ditemukan.")
    return True


def is_group_allowed(jid: str) -> bool:
    return repo.is_group_active(jid)


def note_group_seen(jid: str, name: str):
    repo.upsert_seen_group(jid, name)
