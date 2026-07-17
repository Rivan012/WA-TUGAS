import logging
from datetime import datetime

from backend.firebase_service import db
from backend.services.whatsapp_service import send_message

logger = logging.getLogger("reminder_job")

# Tahapan reminder, diurutkan dari paling jauh ke paling dekat deadline.
# field       : nama field boolean di Firestore buat nandain sudah terkirim
# threshold   : kirim reminder kalau sisa waktu <= sekian menit dari deadline
# label       : label yang tampil di pesan WA
STAGES = [
    {"field": "reminder_h3", "threshold_minutes": 3 * 24 * 60, "label": "H-3"},
    {"field": "reminder_h1", "threshold_minutes": 1 * 24 * 60, "label": "H-1"},
    {"field": "reminder_1jam", "threshold_minutes": 60, "label": "H-1 Jam"},
]


def _parse_deadline(raw_deadline):
    """Parse deadline ISO string. Return None kalau kosong/format invalid."""
    if not raw_deadline:
        return None
    try:
        return datetime.fromisoformat(raw_deadline)
    except (ValueError, TypeError):
        return None


# Toleransi buat stage terakhir: kalau job sempat mati/telat cek, task yang
# baru lewat deadline TIDAK LEBIH DARI ini tetap dapat reminder susulan.
# Kalau lebih dari ini, dianggap task memang sudah lama lewat (misal
# sengaja dibuat dengan deadline masa lalu) -> tidak usah kirim reminder lagi.
OVERDUE_GRACE_MINUTES = 15


def _stage_to_send(menit_tersisa, task, only_fields=None):
    """
    Tentukan stage mana (kalau ada) yang harus dikirim sekarang.
    Tiap stage punya window sendiri: aktif dari threshold-nya sampai
    sebelum threshold stage berikutnya (yang lebih dekat ke deadline).
    Stage terakhir (paling dekat deadline) punya toleransi OVERDUE_GRACE_MINUTES
    setelah deadline lewat, bukan tanpa batas -- supaya task yang dari awal
    dibuat dengan deadline sudah lewat tidak ikut ke-trigger.

    only_fields: kalau diisi, stage yang field-nya tidak ada di list ini dilewati
    (dianggap "belum masuk giliran job ini"), tetap dicek job lain yang jadwalnya cocok.
    """
    for i, stage in enumerate(STAGES):
        if only_fields is not None and stage["field"] not in only_fields:
            continue  # bukan jatah job ini

        if task.get(stage["field"], False):
            continue  # stage ini sudah pernah dikirim

        if menit_tersisa > stage["threshold_minutes"]:
            continue  # belum masuk window stage ini

        is_last_stage = i == len(STAGES) - 1
        if is_last_stage:
            if menit_tersisa < -OVERDUE_GRACE_MINUTES:
                # Sudah lewat terlalu lama, bukan kasus "server sempat mati" lagi
                continue
        else:
            next_threshold = STAGES[i + 1]["threshold_minutes"]
            if menit_tersisa <= next_threshold:
                # Sudah masuk window stage berikutnya, skip stage ini
                continue

        return stage

    return None


def _process_task(doc, only_fields=None):
    task = doc.to_dict()
    nama = task.get("nama", "(tanpa nama)")
    user_id = task.get("user_id")
    raw_deadline = task.get("deadline")

    if not user_id:
        logger.warning("Task %s tidak punya user_id, skip.", doc.id)
        return

    deadline = _parse_deadline(raw_deadline)
    if deadline is None:
        logger.warning("Task %s format deadline invalid: %r", doc.id, raw_deadline)
        return

    now = datetime.now(deadline.tzinfo) if deadline.tzinfo else datetime.now()
    menit_tersisa = (deadline - now).total_seconds() / 60

    stage = _stage_to_send(menit_tersisa, task, only_fields=only_fields)
    if stage is None:
        return

    logger.info(
        "Task '%s' (id=%s) sisa %.0f menit -> kirim reminder %s",
        nama, doc.id, menit_tersisa, stage["label"],
    )

    berhasil = send_message(
        user_id,
        f"""🚨 REMINDER TUGAS ({stage['label']})\nNama: {nama}\nDeadline: {deadline.strftime('%d-%m-%Y %H:%M')}\n\nSegera kerjakan!""",
    )

    if berhasil:
        doc.reference.update({stage["field"]: True})
        logger.info(
            "Reminder %s task %s berhasil dikirim & status disimpan.",
            stage["label"], doc.id,
        )
    else:
        logger.error(
            "Reminder %s task %s GAGAL dikirim, status tidak diubah, dicoba lagi siklus berikutnya.",
            stage["label"], doc.id,
        )


def check_deadlines(only_fields=None):
    """
    Cek semua task 'belum' dan kirim reminder yang jatuh tempo.

    only_fields: opsional, list nama field stage (mis. ["reminder_h3", "reminder_h1"])
    buat membatasi job ini cuma memproses stage tertentu. None = semua stage.
    Dipakai supaya H-3/H-1 bisa dijadwalkan di jam-jam tetap (lihat scheduler.py),
    sementara H-1 Jam tetap dicek berkala biar presisi ke deadline.
    """
    logger.info("Mengecek deadline... (only_fields=%s)", only_fields)

    try:
        docs = list(
            db.collection("tasks").where("status", "==", "belum").stream()
        )
    except Exception:
        logger.exception("Gagal query Firestore, skip siklus ini.")
        return

    for doc in docs:
        try:
            _process_task(doc, only_fields=only_fields)
        except Exception:
            logger.exception("Error tak terduga memproses task %s", doc.id)

    logger.info("Selesai mengecek %d task.", len(docs))