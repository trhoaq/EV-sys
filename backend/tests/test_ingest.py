from __future__ import annotations

from datetime import datetime, timezone

from backend.extensions import db
from backend.models.entities import Alert, Device, SensorData, Vehicle
from backend.services.fake_session_service import generate_fake_charging_session
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
            },
            use_payload_timestamp=True,
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


def test_ingest_does_not_create_low_current_alert(app):
    with app.app_context():
        result = ingest_sensor_payload(
            {
                "device_id": "charger-02",
                "bien_so_xe": "59A-12345",
                "current": 20,
                "voltage": 220,
                "power": 4400,
            }
        )

        alert = Alert.query.filter_by(device_id=result["device"]["id"]).first()
        assert alert is None


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
            },
            use_payload_timestamp=True,
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


def test_ingest_creates_statistical_anomaly_alert_for_outlier_current(app):
    with app.app_context():
        for offset, current_value in enumerate([118, 121, 119, 120, 122, 117, 118, 121], start=1):
            ingest_sensor_payload(
                {
                    "device_id": "charger-05",
                    "bien_so_xe": "59A-12345",
                    "current": current_value,
                    "voltage": 220,
                    "power": current_value * 220,
                    "timestamp": f"2026-04-09T10:{offset:02d}:00Z",
                },
                use_payload_timestamp=True,
            )

        result = ingest_sensor_payload(
            {
                "device_id": "charger-05",
                "bien_so_xe": "59A-12345",
                "current": 190,
                "voltage": 220,
                "power": 41800,
                "timestamp": "2026-04-09T10:09:00Z",
            },
            use_payload_timestamp=True,
        )

        alert = Alert.query.filter_by(device_id=result["device"]["id"], type="statistical_current_anomaly").first()
        device = Device.query.filter_by(device_code="charger-05").first()

        assert alert is not None
        assert "rolling baseline" in alert.message
        assert device.status == "abnormal"


def test_generated_two_hour_session_triggers_statistical_detection(app):
    with app.app_context():
        upsert_system_settings(8.0, 18.0, None, charging_detection_current_ma=8.5)
        payloads = generate_fake_charging_session(
            device_code="esp32s3_01",
            license_plate="59A-12345",
            duration_minutes=120,
            current_min_a=9.0,
            current_max_a=12.0,
            voltage_min_v=23.0,
            voltage_max_v=25.5,
            anomaly_minutes=[32, 79, 104],
            seed=20260410,
        )

        for payload in payloads:
            ingest_sensor_payload(payload, use_payload_timestamp=True)

        anomaly_alerts = Alert.query.filter_by(type="statistical_current_anomaly").all()
        charger = Device.query.filter_by(device_code="esp32s3_01").first()
        history_count = SensorData.query.filter_by(device_id=charger.id).count()

        assert history_count == 120
        assert len(anomaly_alerts) >= 1
        assert charger.status == "not_charging"
