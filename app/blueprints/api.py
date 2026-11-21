from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models import Category
from app.extensions import db
from app.schemas import EventCreateUpdateSchema, CategorySchema
from app.services import event_service, reminder_service

api_bp = Blueprint("api", __name__)
event_schema = EventCreateUpdateSchema()
category_schema = CategorySchema()


# ==========================================
#  Events Endpoints
# ==========================================

@api_bp.route("/events", methods=["GET"])
def list_events():
    """UC-01, UC-07: Daftar event pada rentang tanggal, dengan filter dan pencarian."""
    start = request.args.get("start")
    end = request.args.get("end")
    category_id = request.args.get("category")
    status = request.args.get("status")
    query_text = request.args.get("q")

    events = event_service.get_events(
        start=start,
        end=end,
        category_id=category_id,
        status=status,
        search=query_text
    )
    return jsonify([e.to_dict() for e in events]), 200


@api_bp.route("/events", methods=["POST"])
def create_event():
    """UC-03, UC-09: Membuat event beserta daftar pengingat."""
    json_data = request.get_json(silent=True) or {}
    try:
        validated = event_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"message": "Validasi gagal", "errors": err.messages}), 422

    event, skipped = event_service.create_event(validated)
    response_data = event.to_dict()
    if skipped > 0:
        response_data["warning"] = f"{skipped} pengingat dilewati karena waktunya sudah lewat."
    return jsonify(response_data), 201


@api_bp.route("/events/<int:event_id>", methods=["GET"])
def get_event(event_id):
    """UC-02: Detail satu event."""
    event = event_service.get_event_by_id(event_id)
    if not event:
        return jsonify({"message": "Event tidak ditemukan"}), 404
    return jsonify(event.to_dict()), 200


@api_bp.route("/events/<int:event_id>", methods=["PUT"])
def update_event(event_id):
    """UC-04, UC-09: Mengubah event."""
    json_data = request.get_json(silent=True) or {}
    try:
        validated = event_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"message": "Validasi gagal", "errors": err.messages}), 422

    event, skipped = event_service.update_event(event_id, validated)
    if not event:
        return jsonify({"message": "Event tidak ditemukan"}), 404

    response_data = event.to_dict()
    if skipped > 0:
        response_data["warning"] = f"{skipped} pengingat dilewati karena waktunya sudah lewat."
    return jsonify(response_data), 200


@api_bp.route("/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    """UC-05: Menghapus event dan pengingatnya."""
    success = event_service.delete_event(event_id)
    if not success:
        return jsonify({"message": "Event tidak ditemukan"}), 404
    return jsonify({"message": "Event berhasil dihapus"}), 200


@api_bp.route("/events/<int:event_id>/status", methods=["PATCH"])
def patch_event_status(event_id):
    """UC-06: Mengubah status (aktif/selesai/dibatalkan)."""
    json_data = request.get_json(silent=True) or {}
    new_status = json_data.get("status")

    if not new_status:
        # Default: toggle aktif <-> selesai
        current = event_service.get_event_by_id(event_id)
        if not current:
            return jsonify({"message": "Event tidak ditemukan"}), 404
        new_status = "selesai" if current.status == "aktif" else "aktif"

    if new_status not in ["aktif", "selesai", "dibatalkan"]:
        return jsonify({"message": "Status harus berupa aktif, selesai, atau dibatalkan"}), 400

    event = event_service.set_event_status(event_id, new_status)
    if not event:
        return jsonify({"message": "Event tidak ditemukan"}), 404
    return jsonify(event.to_dict()), 200


# ==========================================
#  Categories Endpoints (UC-08)
# ==========================================

@api_bp.route("/categories", methods=["GET"])
def list_categories():
    categories = Category.query.order_by(Category.id.asc()).all()
    return jsonify([c.to_dict() for c in categories]), 200


@api_bp.route("/categories", methods=["POST"])
def create_category():
    json_data = request.get_json(silent=True) or {}
    try:
        validated = category_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"message": "Validasi gagal", "errors": err.messages}), 422

    category = Category(
        user_id=1,
        name=validated["name"].strip(),
        color=validated.get("color", "#4f46e5")
    )
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201


@api_bp.route("/categories/<int:category_id>", methods=["PUT"])
def update_category(category_id):
    cat = Category.query.get(category_id)
    if not cat:
        return jsonify({"message": "Kategori tidak ditemukan"}), 404

    json_data = request.get_json(silent=True) or {}
    try:
        validated = category_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"message": "Validasi gagal", "errors": err.messages}), 422

    cat.name = validated["name"].strip()
    if "color" in validated:
        cat.color = validated["color"]
    db.session.commit()
    return jsonify(cat.to_dict()), 200


@api_bp.route("/categories/<int:category_id>", methods=["DELETE"])
def delete_category(category_id):
    cat = Category.query.get(category_id)
    if not cat:
        return jsonify({"message": "Kategori tidak ditemukan"}), 404

    # Aturan bisnis 7.2: Menghapus kategori tidak menghapus event; event tersebut menjadi "Tanpa kategori"
    from app.models import Event
    Event.query.filter_by(category_id=category_id).update({"category_id": None})

    db.session.delete(cat)
    db.session.commit()
    return jsonify({"message": "Kategori berhasil dihapus"}), 200


# ==========================================
#  Reminders Endpoints (UC-10, UC-11)
# ==========================================

@api_bp.route("/reminders/due", methods=["GET"])
def get_due_reminders():
    """UC-10: Pengingat berstatus due (termasuk yang terlewat)."""
    reminders = reminder_service.get_due_reminders()
    return jsonify(reminders), 200


@api_bp.route("/reminders/<int:reminder_id>/ack", methods=["POST"])
def ack_reminder(reminder_id):
    """UC-10: Menandai pengingat delivered."""
    success = reminder_service.ack_reminder(reminder_id)
    if not success:
        return jsonify({"message": "Pengingat tidak ditemukan"}), 404
    return jsonify({"message": "Pengingat ditandai delivered"}), 200


@api_bp.route("/reminders/<int:reminder_id>/snooze", methods=["POST"])
def snooze_reminder(reminder_id):
    """UC-11: Menunda pengingat N menit."""
    json_data = request.get_json(silent=True) or {}
    minutes = int(json_data.get("minutes", 10))
    if minutes <= 0:
        minutes = 10

    new_reminder = reminder_service.snooze_reminder(reminder_id, minutes)
    if not new_reminder:
        return jsonify({"message": "Pengingat tidak ditemukan"}), 404

    return jsonify({
        "message": f"Pengingat ditunda selama {minutes} menit",
        "new_reminder": new_reminder.to_dict()
    }), 200
