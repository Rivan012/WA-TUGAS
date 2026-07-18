import re
from datetime import datetime
from backend.firebase_service import db

COLLECTION = "tasks"


def _group_prefix(group_name: str) -> str:
    """
    Bikin prefix task_id dari nama grup, contoh:
    'Kelas Pemrograman Web A' -> 'KPWA'
    'TugasKuliah'             -> 'TUGA' (1 kata -> 4 huruf pertama)
    Nama kosong/aneh          -> 'GRP' (fallback)
    """
    if not group_name:
        return "GRP"

    words = re.findall(r"[A-Za-z0-9]+", group_name.upper())

    if not words:
        return "GRP"

    if len(words) == 1:
        prefix = words[0][:4]
    else:
        prefix = "".join(w[0] for w in words)[:6]

    return prefix or "GRP"


def generate_task_id(group_id=None, group_name=None):
    # Task pribadi (bukan dari grup) tetap pakai prefix "TSK" seperti sebelumnya.
    # Task dari grup pakai prefix dari nama grupnya sendiri.
    prefix = _group_prefix(group_name) if group_id else "TSK"

    docs = db.collection(COLLECTION).stream()

    max_id = 0

    for doc in docs:
        # task_id juga dipakai sebagai document ID, jadi harus dicek unik
        # secara global (bukan cuma di antara task grup ini) biar gak ada
        # tabrakan/timpa antar grup yang kebetulan prefix-nya sama.
        task_id = doc.id

        if task_id.startswith(prefix):
            try:
                nomor = int(task_id[len(prefix):])
                max_id = max(max_id, nomor)
            except (ValueError, TypeError):
                pass

    return f"{prefix}{max_id+1:03d}"


def create_task(data):
    group_id = data.get("group_id")
    group_name = data.get("group_name")

    task_id = generate_task_id(group_id, group_name)

    data["task_id"] = task_id
    data["status"] = "belum"
    data["created_at"] = datetime.now().isoformat()
    data.setdefault("group_id", None)

    db.collection(COLLECTION).document(task_id).set(data)

    return data


def get_tasks(user_id=None, group_id=None):
    """
    Kalau group_id dikasih -> tampilkan SEMUA tugas yang ditambahkan di grup itu
    (siapapun pengirimnya), karena /list di grup harus jadi daftar bersama.
    Kalau group_id kosong (chat pribadi) -> tampilkan tugas milik user_id itu saja.
    """
    query = db.collection(COLLECTION)

    if group_id:
        query = query.where("group_id", "==", group_id)
    else:
        query = query.where("user_id", "==", user_id).where("group_id", "==", None)

    query = query.where("status", "==", "belum")

    return [doc.to_dict() for doc in query.stream()]


def finish_task(task_id):
    ref = db.collection(COLLECTION).document(task_id)

    if not ref.get().exists:
        return False

    ref.update({"status": "selesai"})
    return True


def delete_task(task_id):
    ref = db.collection(COLLECTION).document(task_id)

    if not ref.get().exists:
        return False

    ref.delete()
    return True