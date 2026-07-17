from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.config import TIMEZONE
from backend.jobs.reminder_job import check_deadlines

scheduler = BackgroundScheduler(timezone=TIMEZONE)


def start_scheduler():
    # H-3 & H-1: dikirim di jam-jam tetap (bukan terus-menerus), sesuai
    # kebutuhan supaya notifikasi tidak random -- jam 12 siang, 22:00, dan 00:00.
    scheduler.add_job(
        check_deadlines,
        CronTrigger(hour="0,12,22", minute=0),
        kwargs={"only_fields": ["reminder_h3", "reminder_h1"]},
        id="reminder_h3_h1",
        replace_existing=True,
    )

    # H-1 Jam: tetap dicek berkala (tiap 5 menit) supaya presisi mendekati deadline,
    # karena stage ini butuh ketepatan jam, bukan jadwal tetap harian.
    scheduler.add_job(
        check_deadlines,
        "interval",
        minutes=5,
        kwargs={"only_fields": ["reminder_1jam"]},
        id="reminder_1jam",
        replace_existing=True,
    )

    scheduler.start()

    print("✅ Scheduler berjalan... (H-3/H-1: jam 00:00, 12:00, 22:00 | H-1 Jam: tiap 5 menit)")
