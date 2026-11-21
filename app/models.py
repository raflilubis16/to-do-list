from datetime import datetime, timezone
from .extensions import db


def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, default="Pengguna")
    email = db.Column(db.String(120), unique=True, nullable=False, default="user@localhost")
    password_hash = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_naive)

    categories = db.relationship("Category", back_populates="user", cascade="all, delete-orphan")
    events = db.relationship("Event", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, default=1)
    name = db.Column(db.String(80), nullable=False)
    color = db.Column(db.String(20), nullable=False, default="#4f46e5")
    created_at = db.Column(db.DateTime, default=utcnow_naive)

    user = db.relationship("User", back_populates="categories")
    events = db.relationship("Event", back_populates="category")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, default=1)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    start_at = db.Column(db.DateTime, nullable=False)  # Disimpan dalam UTC
    end_at = db.Column(db.DateTime, nullable=True)     # Disimpan dalam UTC
    all_day = db.Column(db.Boolean, default=False, nullable=False)
    priority = db.Column(db.String(12), default="sedang", nullable=False)  # rendah, sedang, tinggi
    status = db.Column(db.String(12), default="aktif", nullable=False)      # aktif, selesai, dibatalkan
    created_at = db.Column(db.DateTime, default=utcnow_naive)
    updated_at = db.Column(db.DateTime, default=utcnow_naive, onupdate=utcnow_naive)

    user = db.relationship("User", back_populates="events")
    category = db.relationship("Category", back_populates="events")
    reminders = db.relationship("Reminder", back_populates="event", cascade="all, delete-orphan", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "Tanpa kategori",
            "category_color": self.category.color if self.category else "#64748b",
            "title": self.title,
            "description": self.description or "",
            "location": self.location or "",
            "start_at": self.start_at.isoformat() + "Z" if self.start_at else None,
            "end_at": self.end_at.isoformat() + "Z" if self.end_at else None,
            "all_day": self.all_day,
            "priority": self.priority,
            "status": self.status,
            "reminders": [r.to_dict() for r in self.reminders],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Reminder(db.Model):
    __tablename__ = "reminders"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    offset_minutes = db.Column(db.Integer, nullable=False, default=0)
    remind_at = db.Column(db.DateTime, nullable=False)  # Disimpan dalam UTC
    status = db.Column(db.String(12), default="pending", nullable=False)  # pending, due, delivered
    delivered_at = db.Column(db.DateTime, nullable=True)

    event = db.relationship("Event", back_populates="reminders")

    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "event_title": self.event.title if self.event else None,
            "offset_minutes": self.offset_minutes,
            "remind_at": self.remind_at.isoformat() + "Z" if self.remind_at else None,
            "status": self.status,
            "delivered_at": self.delivered_at.isoformat() + "Z" if self.delivered_at else None,
        }
