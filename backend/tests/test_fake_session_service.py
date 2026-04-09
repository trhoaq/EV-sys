import json

from backend.services.fake_session_service import generate_fake_payload_fleet


def test_generate_fake_payload_fleet_creates_multiple_devices_and_two_plates(tmp_path):
    payloads = generate_fake_payload_fleet(duration_minutes=10)

    device_codes = {payload["device_id"] for payload in payloads}
    plates = {payload["bien_so_xe"] for payload in payloads}

    assert len(payloads) == 40
    assert len(device_codes) == 4
    assert plates == {"59A-12345", "51B-67890"}

    preview_path = tmp_path / "fleet.jsonl"
    preview_path.write_text("\n".join(json.dumps(payload) for payload in payloads) + "\n", encoding="utf-8")
    assert preview_path.exists()


def test_generate_fake_payload_fleet_has_startup_and_shutdown_shape():
    payloads = generate_fake_payload_fleet(duration_minutes=30)
    first_device_rows = [payload for payload in payloads if payload["device_id"] == "esp32s3_01"]

    assert first_device_rows[0]["current"] < first_device_rows[6]["current"]
    assert first_device_rows[-1]["current"] == 0.0
