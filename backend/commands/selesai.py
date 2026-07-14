from backend.services.task import selesai_task


def execute(message):

    args = message.split()

    if len(args) < 2:
        return "❌ Contoh:\n/selesai TSK001"

    task_id = args[1].upper()

    if selesai_task(task_id):
        return f"✅ Tugas {task_id} selesai."

    return "❌ Task tidak ditemukan."