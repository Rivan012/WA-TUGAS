from backend.services.task import hapus_task


def execute(message):

    args = message.split()

    if len(args) < 2:
        return "❌ Contoh:\n/hapus TSK001"

    task_id = args[1].upper()

    if hapus_task(task_id):
        return f"🗑 Tugas {task_id} berhasil dihapus."

    return "❌ Task tidak ditemukan."