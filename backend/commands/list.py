from backend.services.task import list_task


def execute(user_id, group_id=None):

    tasks = list_task(user_id, group_id)

    if not tasks:
        return "📭 Tidak ada tugas."

    pesan = "📚 *Daftar Tugas Grup*\n\n" if group_id else "📚 *Daftar Tugas*\n\n"

    for task in tasks:

        pesan += (
            f"ID Tugas : {task['task_id']}\n"
            f"Nama Tugas : {task['nama']}\n"
            f"Matkul : {task['matkul']}\n"
            f"Deadline : {task['deadline']}\n"
            f"━━━━━━━━━━━━━━\n"
        )

    return pesan