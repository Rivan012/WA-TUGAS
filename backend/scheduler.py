from apscheduler.schedulers.background import BackgroundScheduler
from backend.jobs.reminder_job import check_deadlines

scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(
        check_deadlines,
        "interval",
        seconds=1800
    )

    scheduler.start()

    print("✅ Scheduler berjalan...")