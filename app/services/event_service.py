from datetime import datetime, timezone, timedelta
from dateutil import parser
from app.extensions import db
from app.models import Event, Reminder, Category


def parse_to_utc(dt_val):
    """Konversi input string atau datetime ke UTC naive datetime."""
    if dt_val is None:
        return None
    if isinstance(dt_val, str):
        parsed = parser.parse(dt_val)
    else:
        parsed = dt_val

    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def get_events(start=None, end=None, category_id=None, status=None, search=None):
    """Mengambil daftar event dengan filter rentang tanggal, kategori, status, dan pencarian kata kunci."""
    query = Event.query

    if start:
        start_utc = parse_to_utc(start)
        # Event berakhir setelah atau saat start_utc (atau mulai setelah/saat start_utc jika end_at None)
        query = query.filter(
            (Event.end_at >= start_utc) | ((Event.end_at == None) & (Event.start_at >= start_utc))
        )

    if end:
        end_utc = parse_to_utc(end)
        # Jika format hanya tanggal YYYY-MM-DD, set ke akhir hari 23:59:59
        if isinstance(end, str) and len(end.strip()) == 10:
            end_utc = end_utc.replace(hour=23, minute=59, second=59, microsecond=999999)
        query = query.filter(Event.start_at <= end_utc)

    if category_id is not None:
        if str(category_id) == "0":
            query = query.filter(Event.category_id == None)
        else:
            query = query.filter(Event.category_id == category_id)

    if status:
        query = query.filter(Event.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Event.title.ilike(search_term)) |
            (Event.description.ilike(search_term)) |
            (Event.location.ilike(search_term))
        )

    return query.order_by(Event.start_at.asc()).all()


def get_event_by_id(event_id):
    return Event.query.get(event_id)


def create_event(data):
    """
    Membuat event baru beserta pengingatnya.
    Aturan bisnis:
    - remind_at = start_at - offset_minutes
    - Jika remind_at sudah lewat saat event disimpan, pengingat tersebut tidak dibuat.
    """
    start_at_utc = parse_to_utc(data["start_at"])
    end_at_utc = parse_to_utc(data.get("end_at"))

    category_id = data.get("category_id")
    if category_id:
        cat = Category.query.get(category_id)
        if not cat:
            category_id = None

    event = Event(
        user_id=1,
        category_id=category_id,
        title=data["title"].strip(),
        description=data.get("description", "").strip(),
        location=data.get("location", "").strip(),
        start_at=start_at_utc,
        end_at=end_at_utc,
        all_day=data.get("all_day", False),
        priority=data.get("priority", "sedang"),
        status=data.get("status", "aktif"),
    )
    db.session.add(event)
    db.session.flush()

    # Buat pengingat
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    offsets = set(data.get("reminders", []))
    skipped_reminders = 0

    for offset in sorted(offsets):
        remind_at = start_at_utc - timedelta(minutes=offset)
        if remind_at < now_utc:
            skipped_reminders += 1
            continue  # Lewati pengingat yang sudah lampau

        reminder = Reminder(
            event_id=event.id,
            offset_minutes=offset,
            remind_at=remind_at,
            status="pending"
        )
        db.session.add(reminder)

    db.session.commit()
    return event, skipped_reminders


def update_event(event_id, data):
    """
    Mengubah event yang sudah ada.
    Aturan bisnis:
    - Jika waktu mulai berubah, remind_at pengingat berstatus pending dihitung ulang.
    """
    event = Event.query.get(event_id)
    if not event:
        return None, 0

    old_start_at = event.start_at
    new_start_at = parse_to_utc(data.get("start_at", event.start_at))
    start_changed = (old_start_at != new_start_at)

    if "title" in data:
        event.title = data["title"].strip()
    if "description" in data:
        event.description = data.get("description", "").strip()
    if "location" in data:
        event.location = data.get("location", "").strip()
    if "start_at" in data:
        event.start_at = new_start_at
    if "end_at" in data:
        event.end_at = parse_to_utc(data.get("end_at"))
    if "all_day" in data:
        event.all_day = data["all_day"]
    if "category_id" in data:
        cat_id = data.get("category_id")
        event.category_id = cat_id if cat_id else None
    if "priority" in data:
        event.priority = data["priority"]
    if "status" in data:
        event.status = data["status"]

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    skipped_reminders = 0

    if "reminders" in data:
        # Jika daftar pengingat disediakan, perbarui daftar pengingat
        # Hapus pengingat pending lama
        for r in list(event.reminders):
            if r.status == "pending":
                db.session.delete(r)

        offsets = set(data.get("reminders", []))
        for offset in sorted(offsets):
            remind_at = event.start_at - timedelta(minutes=offset)
            if remind_at < now_utc:
                skipped_reminders += 1
                continue
            r = Reminder(
                event_id=event.id,
                offset_minutes=offset,
                remind_at=remind_at,
                status="pending"
            )
            db.session.add(r)
    elif start_changed:
        # Jika hanya start_at berubah dan reminders tidak dikirim ulang, hitung ulang remind_at pending
        for r in event.reminders:
            if r.status == "pending":
                r.remind_at = event.start_at - timedelta(minutes=r.offset_minutes)

    db.session.commit()
    return event, skipped_reminders


def delete_event(event_id):
    """Menghapus event beserta pengingatnya (cascade)."""
    event = Event.query.get(event_id)
    if not event:
        return False
    db.session.delete(event)
    db.session.commit()
    return True


def set_event_status(event_id, new_status):
    """Mengubah status event (aktif <-> selesai / dibatalkan)."""
    event = Event.query.get(event_id)
    if not event:
        return None
    event.status = new_status
    db.session.commit()
    return event
