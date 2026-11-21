from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models import Reminder, Event


def get_due_reminders():
    """
    Mengambil pengingat yang berstatus 'due' atau yang waktunya sudah tiba (remind_at <= sekarang dan pending).
    Secara atomik memperbarui pengingat pending yang jatuh tempo menjadi due.
    """
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    # Tandai pending yang jatuh tempo menjadi due
    (
        Reminder.query
        .filter(Reminder.status == "pending", Reminder.remind_at <= now_utc)
        .update({"status": "due"}, synchronize_session=False)
    )
    db.session.commit()

    # Ambil semua pengingat yang berstatus due
    due_reminders = (
        Reminder.query
        .join(Event)
        .filter(Reminder.status == "due")
        .order_by(Reminder.remind_at.asc())
        .all()
    )

    result = []
    for r in due_reminders:
        d = r.to_dict()
        d["event"] = r.event.to_dict() if r.event else None
        result.append(d)

    return result


def ack_reminder(reminder_id):
    """Menandai pengingat delivered saat pengguna menutup atau melihat detail notifikasi."""
    reminder = Reminder.query.get(reminder_id)
    if not reminder:
        return False
    reminder.status = "delivered"
    reminder.delivered_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()
    return True


def snooze_reminder(reminder_id, minutes=10):
    """
    Menunda pengingat selama N menit:
    - Reminder lama diubah statusnya menjadi delivered
    - Dibuat reminder baru berstatus pending dengan remind_at = sekarang + N menit
    """
    reminder = Reminder.query.get(reminder_id)
    if not reminder:
        return None

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    reminder.status = "delivered"
    reminder.delivered_at = now_utc

    new_remind_at = now_utc + timedelta(minutes=minutes)
    new_reminder = Reminder(
        event_id=reminder.event_id,
        offset_minutes=reminder.offset_minutes,
        remind_at=new_remind_at,
        status="pending"
    )
    db.session.add(new_reminder)
    db.session.commit()
    return new_reminder
