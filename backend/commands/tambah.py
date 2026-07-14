from datetime import datetime
 
from backend.utils.parser import parse_task
from backend.services.ai_parser import parse_task_ai
from backend.services.task import tambah_task
 
 
def _is_format_manual(body: str) -> bool:
    """
    True kalau body kelihatan seperti format kaku key: value
    (minimal ada baris 'nama:' atau 'matkul:' atau 'deadline:').
    """
    lower = body.lower()
    return any(
        line.strip().startswith(("nama:", "matkul:", "deadline:", "catatan:"))
        for line in lower.splitlines()
    )
 
 
def execute(user_id, message):
 
    body = message.replace("/tambah", "").strip()
 
    if not body:
        return "❌ Format kosong. Contoh: /tambah tugas kalkulus besok jam 8 malam"
 
    task = {}
 
    if _is_format_manual(body):
        # Format kaku terdeteksi -> langsung parse manual, skip AI sama sekali
        task = parse_task(body)
    else:
        # Bahasa bebas -> coba AI
        try:
            task = parse_task_ai(body)
        except Exception as e:
            print(f"[tambah] AI parser gagal, fallback ke format manual: {e}")
 
        # Kalau AI gagal atau hasilnya gak lengkap, coba parser format kaku juga
        # (jaga-jaga kalau user sebenarnya nulis format manual tapi typo/gak terdeteksi)
        if not all(k in task and task[k] for k in ("nama", "matkul", "deadline")):
            task = parse_task(body)
 
    if "nama" not in task or not task["nama"]:
        return "❌ Field 'nama' wajib diisi."
 
    if "matkul" not in task or not task["matkul"]:
        return "❌ Field 'matkul' wajib diisi."
 
    if "deadline" not in task or not task["deadline"]:
        return "❌ Field 'deadline' wajib diisi."
 
    try:
        deadline_dt = datetime.fromisoformat(task["deadline"])
        deadline_cmp = deadline_dt.replace(tzinfo=None) if deadline_dt.tzinfo else deadline_dt
        if deadline_cmp <= datetime.now():
            return "❌ Deadline tidak boleh di masa lalu. Cek lagi tanggal/jamnya."
    except (ValueError, TypeError):
        return "❌ Format deadline tidak valid."
 
    if "catatan" not in task:
        task["catatan"] = ""
 
    hasil = tambah_task(user_id, task)

    return f"""✅ Tugas berhasil ditambahkan\nId Task : {hasil['task_id']}\nNama Tugas : {hasil['nama']}\nMata Kuliah: {hasil['matkul']}\nDeadline   : {hasil['deadline']}
            """