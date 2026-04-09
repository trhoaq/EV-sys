from backend.services.alert_service import upsert_system_settings
from backend.services.ingest_service import ingest_sensor_payload


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
