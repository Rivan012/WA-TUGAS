from backend.repositories.task_repository import *


def tambah_task(user_id, data, group_id=None, group_name=None):
    data["user_id"] = user_id
    data["group_id"] = group_id
    if group_id:
        data["group_name"] = group_name
    return create_task(data)


def list_task(user_id, group_id=None):
    return get_tasks(user_id, group_id)


def selesai_task(task_id):
    return finish_task(task_id)


def hapus_task(task_id):
    return delete_task(task_id)