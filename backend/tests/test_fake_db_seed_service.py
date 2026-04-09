from backend.models.entities import SensorData, User, Vehicle
from backend.services.fake_db_seed_service import load_fake_payloads_to_db
from backend.services.fake_session_service import generate_fake_payload_fleet


def test_load_fake_payloads_to_db_writes_history_and_ensures_demo_users(app, tmp_path):
    preview_path = tmp_path / "fake_payloads_latest.jsonl"
    payloads = generate_fake_payload_fleet(duration_minutes=5)

    with app.app_context():
        summary = load_fake_payloads_to_db(payloads=payloads, preview_path=preview_path)

        assert summary["rows_loaded"] == 20
        assert summary["device_count"] == 4
        assert summary["license_plate_count"] == 2
        assert SensorData.query.count() == 20
        assert User.query.filter_by(email="user1@example.com").first().check_password("123456")
        assert User.query.filter_by(email="user2@example.com").first().check_password("123456")
        assert Vehicle.query.filter_by(license_plate="59A-12345").first() is not None
        assert Vehicle.query.filter_by(license_plate="51B-67890").first() is not None
