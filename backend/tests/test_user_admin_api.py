from datetime import datetime, timedelta, timezone

from backend.models import ChargingSession
from backend.services.alert_service import upsert_system_settings
from backend.services.fake_db_seed_service import load_fake_payloads_to_db
from backend.services.ingest_service import ingest_sensor_payload
from backend.services.fake_session_service import generate_fake_payload_fleet


def test_user_cannot_view_history_for_other_plate(client, user1_token):
    response = client.get(
        "/api/user/history?plate=51B-67890",
        headers={"Authorization": f"Bearer {user1_token}"},
    )

    assert response.status_code == 403


def test_admin_can_update_global_settings(client, admin_token):
    response = client.put(
        "/api/admin/settings",
        json={
            "min_current_ma": 40,
            "charging_detection_current_ma": 80,
            "max_current_ma": 300,
            "updated_by": "admin@example.com",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["settings"]["max_current_ma"] == 300
    assert body["settings"]["charging_detection_current_ma"] == 80


def test_admin_can_assign_vehicle_to_user(client, admin_token):
    response = client.post(
        "/api/admin/vehicles/assign",
        json={
            "user_email": "user1@example.com",
            "license_plate": "88A-99999",
            "display_name": "Xe moi",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["vehicle"]["license_plate"] == "88A-99999"


def test_user_history_ignores_readings_below_detection_threshold(app, client, user1_token):
    with app.app_context():
        upsert_system_settings(50, 500, None, charging_detection_current_ma=100)
        ingest_sensor_payload(
            {
                "device_id": "charger-01",
                "bien_so_xe": "59A-12345",
                "current": 80,
                "voltage": 220,
                "power": 17600,
                "timestamp": "2026-04-09T10:04:00Z",
            }
        )
        ingest_sensor_payload(
            {
                "device_id": "charger-01",
                "bien_so_xe": "59A-12345",
                "current": 150,
                "voltage": 220,
                "power": 33000,
                "timestamp": "2026-04-09T10:05:00Z",
            }
        )

    response = client.get(
        "/api/user/history?plate=59A-12345",
        headers={"Authorization": f"Bearer {user1_token}"},
    )

    assert response.status_code == 200
    items = response.get_json()["items"]
    assert len(items) == 1
    assert items[0]["current"] == 150


def test_admin_can_view_device_history_without_active_plate(app, client, admin_token):
    with app.app_context():
        ingest_sensor_payload(
            {
                "device_id": "charger-02",
                "current": 30,
                "voltage": 220,
                "power": 6600,
                "timestamp": "2026-04-09T10:06:00Z",
            }
        )

    response = client.get(
        "/api/admin/history?device_code=charger-02",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    items = response.get_json()["items"]
    assert len(items) == 1
    assert items[0]["device_code"] == "charger-02"
    assert items[0]["license_plate"] is None


def test_admin_devices_keeps_statistical_anomaly_status(app, client, admin_token):
    with app.app_context():
        base_time = datetime.now(timezone.utc).replace(second=0, microsecond=0) - timedelta(minutes=8)
        for offset, current_value in enumerate([118, 121, 119, 120, 122, 117, 118, 121], start=1):
            ingest_sensor_payload(
                {
                    "device_id": "charger-06",
                    "bien_so_xe": "59A-12345",
                    "current": current_value,
                    "voltage": 220,
                    "power": current_value * 220,
                    "timestamp": (base_time + timedelta(minutes=offset - 1)).isoformat().replace("+00:00", "Z"),
                },
                use_payload_timestamp=True,
            )

        ingest_sensor_payload(
            {
                "device_id": "charger-06",
                "bien_so_xe": "59A-12345",
                "current": 190,
                "voltage": 220,
                "power": 41800,
                "timestamp": (base_time + timedelta(minutes=8)).isoformat().replace("+00:00", "Z"),
            },
            use_payload_timestamp=True,
        )

    response = client.get(
        "/api/admin/devices",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    charger = next(item for item in response.get_json()["items"] if item["device_code"] == "charger-06")
    assert charger["status"] == "abnormal"


def test_user_can_view_payment_history_for_completed_sessions(app, client, user1_token):
    with app.app_context():
        upsert_system_settings(8.0, 18.0, None, charging_detection_current_ma=8.5)
        payloads = generate_fake_payload_fleet(duration_minutes=30, seed=20260410)
        load_fake_payloads_to_db(payloads=payloads, write_preview_file=False)
        sessions = ChargingSession.query.filter(ChargingSession.status == "completed").all()
        assert sessions

    response = client.get(
        "/api/user/payment-history",
        headers={"Authorization": f"Bearer {user1_token}"},
    )

    assert response.status_code == 200
    items = response.get_json()["items"]
    assert items
    assert all(item["license_plate"] == "59A-12345" for item in items)
    assert all(item["total_vnd"] >= 0 for item in items)
