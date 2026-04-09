from __future__ import annotations

import json
from pathlib import Path

from backend.extensions import db
from backend.models.entities import Alert, SensorData, User, Vehicle
from backend.services.fake_session_service import generate_fake_charging_session, generate_fake_payload_fleet
from backend.services.ingest_service import ingest_sensor_payload

DEFAULT_DEMO_USERS = [
    ("user1@example.com", "123456", "59A-12345"),
    ("user2@example.com", "123456", "51B-67890"),
]


def ensure_fake_demo_users() -> list[User]:
    users = []
    for email, password, license_plate in DEFAULT_DEMO_USERS:
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(email=email, role="user")
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
        else:
            user.set_password(password)
        vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()
        if vehicle is None:
            vehicle = Vehicle(
                user_id=user.id,
                license_plate=license_plate,
                display_name=license_plate,
                is_active=True,
            )
            db.session.add(vehicle)
        else:
            vehicle.user_id = user.id
            vehicle.display_name = license_plate
            vehicle.is_active = True

        users.append(user)

    db.session.commit()
    return users


def load_fake_payloads_to_db(
    *,
    payloads: list[dict],
    preview_path: str | Path | None = None,
    write_preview_file: bool = True,
) -> dict:
    ensure_fake_demo_users()

    if write_preview_file and preview_path is not None:
        output_path = Path(preview_path)
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "\n".join(json.dumps(payload, ensure_ascii=True) for payload in payloads) + "\n",
            encoding="utf-8",
        )
    else:
        output_path = None

    for payload in payloads:
        ingest_sensor_payload(payload, use_payload_timestamp=True, emit_events=False)

    device_codes = sorted({payload["device_id"] for payload in payloads})
    plates = sorted({payload["bien_so_xe"] for payload in payloads})

    return {
        "rows_loaded": len(payloads),
        "device_count": len(device_codes),
        "license_plate_count": len(plates),
        "devices": device_codes,
        "license_plates": plates,
        "sensor_rows": SensorData.query.count(),
        "alert_rows": Alert.query.count(),
        "preview_path": str(output_path) if output_path else None,
    }


def build_fake_payloads(
    *,
    single_device: bool,
    device_code: str,
    license_plate: str,
    duration_minutes: int,
    current_min_a: float,
    current_max_a: float,
    voltage_min_v: float,
    voltage_max_v: float,
    anomaly_minutes: list[int],
    seed: int,
) -> list[dict]:
    if single_device:
        return generate_fake_charging_session(
            device_code=device_code,
            license_plate=license_plate,
            duration_minutes=duration_minutes,
            current_min_a=current_min_a,
            current_max_a=current_max_a,
            voltage_min_v=voltage_min_v,
            voltage_max_v=voltage_max_v,
            anomaly_minutes=anomaly_minutes,
            seed=seed,
        )

    return generate_fake_payload_fleet(
        duration_minutes=duration_minutes,
        current_min_a=current_min_a,
        current_max_a=current_max_a,
        voltage_min_v=voltage_min_v,
        voltage_max_v=voltage_max_v,
        seed=seed,
    )
