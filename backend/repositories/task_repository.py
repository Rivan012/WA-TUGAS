from datetime import datetime
from backend.firebase_service import db

COLLECTION = "tasks"


def generate_task_id():
    docs = db.collection(COLLECTION).stream()

    max_id = 0

    for doc in docs:
        data = doc.to_dict()

        if "task_id" in data:
            try:
                nomor = int(data["task_id"].replace("TSK", ""))
                max_id = max(max_id, nomor)
            except:
                pass

    return f"TSK{max_id+1:03d}"


def create_task(data):
    task_id = generate_task_id()

    data["task_id"] = task_id
    data["status"] = "belum"
    data["created_at"] = datetime.now().isoformat()

    db.collection(COLLECTION).document(task_id).set(data)

    return data


def get_tasks(user_id):
    docs = (
        db.collection(COLLECTION)
        .where("user_id", "==", user_id)
        .where("status", "==", "belum")
        .stream()
    )

    return [doc.to_dict() for doc in docs]


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