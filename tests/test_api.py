import json
from datetime import datetime, timedelta, timezone


def test_get_categories(client):
    res = client.get("/api/categories")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) >= 4  # Default categories: Pekerjaan, Pribadi, Belajar, Kesehatan


def test_create_category(client):
    res = client.post("/api/categories", json={
        "name": "Hobi",
        "color": "#8b5cf6"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["name"] == "Hobi"
    assert data["color"] == "#8b5cf6"


def test_create_category_invalid(client):
    res = client.post("/api/categories", json={"name": ""})
    assert res.status_code == 422


def test_create_and_get_event(client):
    start = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=1, hours=2)).isoformat()

    payload = {
        "title": "Rapat Koordinasi",
        "start_at": start,
        "end_at": end,
        "location": "Ruang Rapat A",
        "description": "Membahas progres proyek",
        "category_id": 1,
        "priority": "tinggi",
        "reminders": [30, 60]
    }

    res = client.post("/api/events", json=payload)
    assert res.status_code == 201
    event = res.get_json()
    assert event["title"] == "Rapat Koordinasi"
    assert event["priority"] == "tinggi"
    assert len(event["reminders"]) == 2

    # Get by ID
    res_get = client.get(f"/api/events/{event['id']}")
    assert res_get.status_code == 200
    assert res_get.get_json()["id"] == event["id"]


def test_update_event(client):
    start = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    payload = {
        "title": "Event Awal",
        "start_at": start,
        "priority": "rendah"
    }
    create_res = client.post("/api/events", json=payload)
    event_id = create_res.get_json()["id"]

    update_payload = {
        "title": "Event Telah Diubah",
        "start_at": start,
        "priority": "tinggi"
    }
    res = client.put(f"/api/events/{event_id}", json=update_payload)
    assert res.status_code == 200
    assert res.get_json()["title"] == "Event Telah Diubah"
    assert res.get_json()["priority"] == "tinggi"


def test_patch_event_status(client):
    start = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    create_res = client.post("/api/events", json={
        "title": "Tugas Belum Selesai",
        "start_at": start
    })
    event_id = create_res.get_json()["id"]

    # Toggle to selesai
    res = client.patch(f"/api/events/{event_id}/status", json={"status": "selesai"})
    assert res.status_code == 200
    assert res.get_json()["status"] == "selesai"

    # Toggle back to aktif
    res2 = client.patch(f"/api/events/{event_id}/status", json={})
    assert res2.status_code == 200
    assert res2.get_json()["status"] == "aktif"


def test_delete_event(client):
    start = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    create_res = client.post("/api/events", json={
        "title": "Event Mau Dihapus",
        "start_at": start
    })
    event_id = create_res.get_json()["id"]

    del_res = client.delete(f"/api/events/{event_id}")
    assert del_res.status_code == 200

    # Pastikan sudah 404
    get_res = client.get(f"/api/events/{event_id}")
    assert get_res.status_code == 404
