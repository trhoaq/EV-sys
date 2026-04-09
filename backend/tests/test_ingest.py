from __future__ import annotations

from datetime import datetime, timezone

from backend.extensions import db
from backend.models.entities import Alert, Device, SensorData, Vehicle
from backend.services.alert_service import upsert_system_settings
from backend.services.ingest_service import ingest_sensor_payload


def test_ingest_creates_sensor_data_and_alert(app):
    with app.app_context():
        vehicle = Vehicle.query.filter_by(license_plate="59A-12345").first()
        result = ingest_sensor_payload(
            {
                "device_id": "charger-01",
                "bien_so_xe": "59A-12345",
                "current": 650,
                "voltage": 220,
                "power": 143000,
                "timestamp": "2026-04-09T10:02:00Z",
            }
        )

        assert result["vehicle"]["license_plate"] == "59A-12345"
        assert Device.query.filter_by(device_code="charger-01").count() == 1
        assert SensorData.query.filter_by(vehicle_id=vehicle.id).count() == 1
        assert Alert.query.filter_by(vehicle_id=vehicle.id, type="high_current").count() == 1


def test_ingest_rejects_payload_without_license_plate(app):
    with app.app_context():
        result = ingest_sensor_payload(
            {
                "device_id": "charger-02",
                "current": 120,
                "voltage": 220,
                "power": 26400,
            }
        )

        assert result["vehicle"] is None
        assert Device.query.filter_by(device_code="charger-02").count() == 1


def test_ingest_ignores_plate_when_current_is_below_detection_threshold(app):
    with app.app_context():
        upsert_system_settings(50, 500, None, charging_detection_current_ma=100)
        vehicle = Vehicle.query.filter_by(license_plate="59A-12345").first()

        result = ingest_sensor_payload(
            {
                "device_id": "charger-03",
                "bien_so_xe": "59A-12345",
                "current": 80,
                "voltage": 220,
                "power": 17600,
                "timestamp": "2026-04-09T10:03:00Z",
            }
        )

        assert result["vehicle"] is None
        assert SensorData.query.filter_by(vehicle_id=vehicle.id).count() == 0


def test_ingest_accepts_unix_epoch_timestamp(app):
    with app.app_context():
        before_ingest = datetime.now(timezone.utc)
        result = ingest_sensor_payload(
            {
                "device_id": "charger-04",
                "current": 120,
                "voltage": 220,
                "power": 26400,
                "timestamp": 1775701407.453681,
            }
        )
        after_ingest = datetime.now(timezone.utc)

        reading = db.session.get(SensorData, result["reading"]["id"])
        assert reading is not None
        assert isinstance(reading.timestamp, datetime)
        normalized_timestamp = (
            reading.timestamp
            if reading.timestamp.tzinfo is not None
            else reading.timestamp.replace(tzinfo=timezone.utc)
        )
        assert before_ingest <= normalized_timestamp <= after_ingest
