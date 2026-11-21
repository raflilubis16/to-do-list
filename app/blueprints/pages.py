from flask import Blueprint, render_template, abort
from app.models import Category, Event
from app.services import event_service

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def dashboard():
    """Halaman Dashboard Utama: Sidebar, Kalender, Panel Detail Event, Toast Notifikasi."""
    categories = Category.query.order_by(Category.id.asc()).all()
    return render_template("dashboard.html", categories=categories)


@pages_bp.route("/events/new")
def new_event():
    """Halaman form tambah event langsung (atau dapat diakses via tautan)."""
    categories = Category.query.order_by(Category.id.asc()).all()
    return render_template("events_form.html", categories=categories, event=None, mode="create")


@pages_bp.route("/events/<int:event_id>")
def event_detail(event_id):
    """Halaman detail satu event (dapat dibuka langsung dari tautan / bookmark)."""
    event = event_service.get_event_by_id(event_id)
    if not event:
        abort(404)
    return render_template("events_detail.html", event=event)


@pages_bp.route("/events/<int:event_id>/edit")
def edit_event(event_id):
    """Halaman edit event."""
    event = event_service.get_event_by_id(event_id)
    if not event:
        abort(404)
    categories = Category.query.order_by(Category.id.asc()).all()
    return render_template("events_form.html", categories=categories, event=event, mode="edit")


@pages_bp.route("/settings")
def settings():
    """Halaman Pengaturan: Kelola kategori, preferensi pengingat bawaan, izin notifikasi."""
    categories = Category.query.order_by(Category.id.asc()).all()
    return render_template("settings.html", categories=categories)
