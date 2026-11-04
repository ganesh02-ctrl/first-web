"""APScheduler jobs. Run ONE backend process with the scheduler enabled (dedupe keys guard repeats)."""
import atexit
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def _in_context(app, func):
    def runner():
        with app.app_context():
            try:
                func()
            except Exception:  # noqa: BLE001
                logger.exception("Scheduled job %s failed", func.__name__)
                from app.extensions import db
                db.session.rollback()
    return runner


def start_scheduler(app) -> BackgroundScheduler | None:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    from app.services.auth import purge_expired_tokens
    from app.services.notification import process_pending_deliveries
    from app.services.reminder import run_deadline_reminders

    tz = app.config["APP_TIMEZONE"]
    sched = BackgroundScheduler(timezone=tz, job_defaults={"coalesce": True, "max_instances": 1,
                                                           "misfire_grace_time": 3600})
    sched.add_job(_in_context(app, run_deadline_reminders), CronTrigger(hour=app.config["REMINDER_RUN_HOUR"],
                  minute=0, timezone=tz), id="deadline_reminders", replace_existing=True)
    sched.add_job(_in_context(app, process_pending_deliveries), "interval",
                  minutes=app.config["DELIVERY_RETRY_INTERVAL_MINUTES"], id="deliveries", replace_existing=True)
    sched.add_job(_in_context(app, purge_expired_tokens), CronTrigger(hour=3, minute=30, timezone=tz),
                  id="purge_tokens", replace_existing=True)
    sched.start()
    atexit.register(lambda: sched.shutdown(wait=False))
    _scheduler = sched
    logger.info("Scheduler started (timezone %s)", tz)
    return sched
