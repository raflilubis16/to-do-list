from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class CategorySchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=80, error="Nama kategori tidak boleh kosong."))
    color = fields.Str(required=False, validate=validate.Regexp(r"^#[0-9a-fA-F]{6}$", error="Format warna harus kode hex (#RRGGBB)."))
    created_at = fields.DateTime(dump_only=True)


class ReminderSchema(Schema):
    id = fields.Int(dump_only=True)
    event_id = fields.Int(dump_only=True)
    offset_minutes = fields.Int(required=True, validate=validate.Range(min=0, error="Offset pengingat tidak boleh negatif."))
    remind_at = fields.DateTime(dump_only=True)
    status = fields.Str(dump_only=True)
    delivered_at = fields.DateTime(dump_only=True)


class EventCreateUpdateSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=120, error="Judul event tidak boleh kosong (maksimal 120 karakter)."))
    description = fields.Str(allow_none=True)
    location = fields.Str(allow_none=True)
    start_at = fields.DateTime(required=True, error_messages={"required": "Waktu mulai harus diisi."})
    end_at = fields.DateTime(allow_none=True)
    all_day = fields.Bool()
    category_id = fields.Int(allow_none=True)
    priority = fields.Str(
        validate=validate.OneOf(["rendah", "sedang", "tinggi"], error="Prioritas harus rendah, sedang, atau tinggi.")
    )
    status = fields.Str(
        validate=validate.OneOf(["aktif", "selesai", "dibatalkan"], error="Status harus aktif, selesai, atau dibatalkan.")
    )
    reminders = fields.List(fields.Int(validate=validate.Range(min=0)))

    @validates_schema
    def validate_times(self, data, **kwargs):
        start = data.get("start_at")
        end = data.get("end_at")
        all_day = data.get("all_day", False)

        if not all_day and start and end:
            if end < start:
                raise ValidationError("Waktu selesai tidak boleh lebih awal dari waktu mulai.", "end_at")
