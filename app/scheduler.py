from datetime import datetime, timezone
import logging
from app.extensions import db, scheduler
from app.models import Reminder

logger = logging.getLogger(__name__)


def mark_due_reminders(app):
    """Pekerjaan otomatis tiap menit yang menandai pengingat jatuh tempo."""
    with app.app_context():
        try:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            updated = (
                Reminder.query
                .filter(Reminder.status == "pending", Reminder.remind_at <= now)
                .update({"status": "due"}, synchronize_session=False)
            )
            if updated > 0:
                db.session.commit()
                logger.info(f"Ditandai {updated} pengingat menjadi 'due'.")
        except Exception as e:
            logger.error(f"Error saat mengecek pengingat: {e}")
            db.session.rollback()


def init_scheduler(app):
    """Inisialisasi APScheduler background job."""
    if not scheduler.running:
        scheduler.add_job(
            id="mark_due_reminders",
            func=mark_due_reminders,
            args=[app],
            trigger="interval",
            seconds=60,
            replace_existing=True,
        )
        scheduler.start()
        logger.info("APScheduler dimulai untuk pengecekan pengingat setiap 60 detik.")
