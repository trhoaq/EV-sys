from backend.models import Alert, Device, SensorData
from backend.services.mqtt_service import ingest_sensor_payload


def test_ingest_sensor_payload_saves_sensor_data(app):
    payload = {
        "device_id": "charger-01",
        "bien_so_xe": "59A-12345",
        "current": 120,
        "voltage": 220,
        "power": 26400,
        "timestamp": "2026-04-09T10:00:00Z",
    }

    with app.app_context():
        result = ingest_sensor_payload(payload, app=app)

        assert result["sensor_data_id"] is not None
        assert SensorData.query.count() == 1
        device = Device.query.first()
        assert device.device_code == "charger-01"


def test_ingest_sensor_payload_creates_alert_when_current_is_high(app):
    payload = {
        "device_id": "charger-01",
        "bien_so_xe": "59A-12345",
        "current": 700,
        "voltage": 220,
        "power": 154000,
        "timestamp": "2026-04-09T10:00:00Z",
    }

    with app.app_context():
        ingest_sensor_payload(payload, app=app)
        alert = Alert.query.first()
        assert alert.type == "high_current"


def test_ingest_sensor_payload_rejects_missing_plate(app):
    payload = {
        "device_id": "charger-01",
        "current": 700,
        "voltage": 220,
        "power": 154000,
    }

    with app.app_context():
        result = ingest_sensor_payload(payload, app=app)
        assert result["vehicle"] is None
