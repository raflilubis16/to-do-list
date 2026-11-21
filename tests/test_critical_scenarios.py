from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models import Event, Reminder, Category
from app.services import reminder_service, event_service


def test_t01_create_event_valid_data(client):
    """T-01: Menambah event dengan data valid -> Event tersimpan dan tampil di kalender."""
    start = (datetime.now(timezone.utc) + timedelta(days=3)).replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=2)

    payload = {
        "title": "Presentasi Proyek Akhir",
        "start_at": start.isoformat(),
        "end_at": end.isoformat(),
        "location": "Auditorium Lantai 3",
        "description": "Membawa slide presentasi dan laptop.",
        "category_id": 1,
        "priority": "tinggi",
        "reminders": [30]
    }

    res = client.post("/api/events", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["title"] == "Presentasi Proyek Akhir"
    assert data["location"] == "Auditorium Lantai 3"
    assert len(data["reminders"]) == 1

    # Cek muncul di query daftar kalender
    list_res = client.get(f"/api/events?start={start.date().isoformat()}&end={(start + timedelta(days=1)).date().isoformat()}")
    assert list_res.status_code == 200
    events = list_res.get_json()
    assert any(e["id"] == data["id"] for e in events)


def test_t02_end_time_before_start_time_rejected(client):
    """T-02: Waktu selesai lebih awal dari waktu mulai -> Ditolak dengan pesan kesalahan yang jelas."""
    start = datetime.now(timezone.utc) + timedelta(days=1, hours=10)
    end = datetime.now(timezone.utc) + timedelta(days=1, hours=8)  # 2 jam lebih awal!

    payload = {
        "title": "Jadwal Tidak Valid",
        "start_at": start.isoformat(),
        "end_at": end.isoformat(),
        "all_day": False
    }

    res = client.post("/api/events", json=payload)
    assert res.status_code == 422
    data = res.get_json()
    assert "errors" in data
    assert "end_at" in data["errors"]
    assert "tidak boleh lebih awal" in data["errors"]["end_at"][0]


def test_t03_delete_event_cascades_reminders(client, app):
    """T-03: Menghapus event yang memiliki pengingat -> Event dan semua pengingatnya terhapus."""
    start = datetime.now(timezone.utc) + timedelta(days=2)
    payload = {
        "title": "Event Dengan Pengingat",
        "start_at": start.isoformat(),
        "reminders": [10, 30, 60]
    }

    res = client.post("/api/events", json=payload)
    assert res.status_code == 201
    event_id = res.get_json()["id"]

    with app.app_context():
        # Verifikasi pengingat tersimpan di DB
        reminders_count = Reminder.query.filter_by(event_id=event_id).count()
        assert reminders_count == 3

    # Hapus event
    del_res = client.delete(f"/api/events/{event_id}")
    assert del_res.status_code == 200

    with app.app_context():
        assert Event.query.get(event_id) is None
        # Semua pengingat harus ikut terhapus (cascade)
        assert Reminder.query.filter_by(event_id=event_id).count() == 0


def test_t04_due_reminder_triggers(client, app):
    """T-04: Waktu pengingat tiba -> Status berubah menjadi due dan tampil di browser."""
    # Buat event dengan waktu mulai sebentar lagi, dan remind_at sekarang atau lampau
    with app.app_context():
        ev = Event(
            user_id=1,
            title="Event Mau Mulai",
            start_at=datetime.utcnow() + timedelta(minutes=5),
            status="aktif"
        )
        db.session.add(ev)
        db.session.flush()

        # Reminder yang waktu remind_at nya sudah tiba (5 menit yang lalu)
        rem = Reminder(
            event_id=ev.id,
            offset_minutes=10,
            remind_at=datetime.utcnow() - timedelta(minutes=5),
            status="pending"
        )
        db.session.add(rem)
        db.session.commit()
        rem_id = rem.id

    # Panggil /api/reminders/due (seperti polling browser)
    res = client.get("/api/reminders/due")
    assert res.status_code == 200
    due_list = res.get_json()
    assert any(r["id"] == rem_id for r in due_list)

    with app.app_context():
        updated_rem = Reminder.query.get(rem_id)
        assert updated_rem.status == "due"


def test_t05_snooze_reminder_10_minutes(client, app):
    """T-05: Menekan Tunda 10 menit -> Pengingat baru dibuat dengan remind_at 10 menit kemudian."""
    with app.app_context():
        ev = Event(
            user_id=1,
            title="Event Ditunda",
            start_at=datetime.utcnow() + timedelta(hours=1),
            status="aktif"
        )
        db.session.add(ev)
        db.session.flush()

        rem = Reminder(
            event_id=ev.id,
            offset_minutes=30,
            remind_at=datetime.utcnow() - timedelta(minutes=1),
            status="due"
        )
        db.session.add(rem)
        db.session.commit()
        rem_id = rem.id

    # Post snooze 10 menit
    res = client.post(f"/api/reminders/{rem_id}/snooze", json={"minutes": 10})
    assert res.status_code == 200
    data = res.get_json()
    assert "new_reminder" in data
    new_rem_id = data["new_reminder"]["id"]

    with app.app_context():
        # Reminder lama harus berstatus delivered
        old_rem = Reminder.query.get(rem_id)
        assert old_rem.status == "delivered"
        assert old_rem.delivered_at is not None

        # Reminder baru harus berstatus pending
        new_rem = Reminder.query.get(new_rem_id)
        assert new_rem.status == "pending"
        # Selisih waktu sekitar 10 menit dari sekarang
        diff = (new_rem.remind_at - datetime.utcnow()).total_seconds()
        assert 500 <= diff <= 650  # ~600 detik (10 menit)


def test_t06_missed_reminder_shown_on_page_open(client, app):
    """T-06: Pengingat jatuh tempo saat halaman tertutup -> Saat halaman dibuka, tampil sebagai terlewat (due)."""
    with app.app_context():
        ev = Event(
            user_id=1,
            title="Event Terlewat Saat Browser Ditutup",
            start_at=datetime.utcnow() + timedelta(hours=2),
            status="aktif"
        )
        db.session.add(ev)
        db.session.flush()

        # Jatuh tempo 2 jam yang lalu saat browser ditutup
        rem = Reminder(
            event_id=ev.id,
            offset_minutes=60,
            remind_at=datetime.utcnow() - timedelta(hours=2),
            status="pending"
        )
        db.session.add(rem)
        db.session.commit()
        rem_id = rem.id

    # Browser dibuka kembali -> memanggil /api/reminders/due
    res = client.get("/api/reminders/due")
    assert res.status_code == 200
    due_list = res.get_json()
    matching = [r for r in due_list if r["id"] == rem_id]
    assert len(matching) == 1
    assert matching[0]["status"] == "due"


def test_t07_event_spanning_midnight(client):
    """T-07: Event melewati tengah malam -> Tampil di kedua hari pada kalender."""
    # Mulai jam 22:00 hari ini, selesai jam 02:00 besok
    day1 = datetime.now(timezone.utc) + timedelta(days=5)
    start = day1.replace(hour=22, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=4)  # Melewati tengah malam ke hari berikutnya

    payload = {
        "title": "Nobar Film Tengah Malam",
        "start_at": start.isoformat(),
        "end_at": end.isoformat()
    }

    res = client.post("/api/events", json=payload)
    assert res.status_code == 201
    event_id = res.get_json()["id"]

    # Filter hari pertama: harus muncul
    res_day1 = client.get(f"/api/events?start={start.date().isoformat()}&end={start.date().isoformat()}")
    assert any(e["id"] == event_id for e in res_day1.get_json())

    # Filter hari kedua: harus muncul juga
    day2_date = (start + timedelta(days=1)).date().isoformat()
    res_day2 = client.get(f"/api/events?start={day2_date}&end={day2_date}")
    assert any(e["id"] == event_id for e in res_day2.get_json())


def test_t08_reschedule_start_time_recalculates_pending_reminders(client, app):
    """T-08: Mengubah waktu mulai event -> remind_at pengingat pending dihitung ulang."""
    # Waktu mulai 3 hari lagi jam 10:00 UTC
    start1 = (datetime.now(timezone.utc) + timedelta(days=3)).replace(hour=10, minute=0, second=0, microsecond=0)
    payload = {
        "title": "Jadwal Rapat Diundur",
        "start_at": start1.isoformat(),
        "reminders": [30]  # remind_at = start1 - 30 menit
    }
    create_res = client.post("/api/events", json=payload)
    assert create_res.status_code == 201
    event_id = create_res.get_json()["id"]

    with app.app_context():
        r1 = Reminder.query.filter_by(event_id=event_id).first()
        expected_r1 = (start1 - timedelta(minutes=30)).replace(tzinfo=None)
        assert abs((r1.remind_at - expected_r1).total_seconds()) < 2

    # Sekarang undur start_at 2 jam ke depan (jam 12:00 UTC)
    start2 = start1 + timedelta(hours=2)
    update_res = client.put(f"/api/events/{event_id}", json={
        "title": "Jadwal Rapat Diundur",
        "start_at": start2.isoformat()
    })
    assert update_res.status_code == 200

    with app.app_context():
        # remind_at harus otomatis dihitung ulang menjadi start2 - 30 menit (jam 11:30 UTC)
        r2 = Reminder.query.filter_by(event_id=event_id).first()
        expected_r2 = (start2 - timedelta(minutes=30)).replace(tzinfo=None)
        assert abs((r2.remind_at - expected_r2).total_seconds()) < 2
