from backend.repositories.task_repository import *


def tambah_task(user_id, data):
    data["user_id"] = user_id
    return create_task(data)


def list_task(user_id):
    return get_tasks(user_id)


def selesai_task(task_id):
    return finish_task(task_id)


def hapus_task(task_id):
    return delete_task(task_id)