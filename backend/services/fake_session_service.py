from __future__ import annotations

import math
import random
import secrets
from datetime import datetime, timedelta, timezone


def resolve_seed(seed: int | None = None) -> int:
    return seed if seed is not None else secrets.randbelow(10_000_000_000)


def generate_fake_charging_session(
    *,
    device_code: str,
    license_plate: str,
    duration_minutes: int = 120,
    current_min_a: float = 9.0,
    current_max_a: float = 12.0,
    voltage_min_v: float = 23.0,
    voltage_max_v: float = 25.5,
    anomaly_minutes: list[int] | None = None,
    start_at: datetime | None = None,
    seed: int | None = None,
) -> list[dict]:
    rng = random.Random(resolve_seed(seed))
    session_start = start_at or datetime.now(timezone.utc).replace(second=0, microsecond=0)
    current_mid = (current_min_a + current_max_a) / 2
    current_amplitude = max((current_max_a - current_min_a) / 2, 0.2)
    voltage_mid = (voltage_min_v + voltage_max_v) / 2
    voltage_amplitude = max((voltage_max_v - voltage_min_v) / 2, 0.1)
    anomaly_points = set(anomaly_minutes or [32, 79, 104])
    startup_minutes = min(5, max(1, duration_minutes // 12))
    shutdown_minutes = min(15, max(3, duration_minutes // 8))

    payloads = []
    for minute_index in range(duration_minutes):
        phase = (2 * math.pi * minute_index) / max(duration_minutes, 1)
        current = current_mid + math.sin(phase * 1.7) * current_amplitude * 0.7 + rng.uniform(-0.22, 0.22)
        voltage = voltage_mid + math.cos(phase * 1.2) * voltage_amplitude * 0.65 + rng.uniform(-0.12, 0.12)

        current = max(current_min_a, min(current_max_a, current))
        voltage = max(voltage_min_v, min(voltage_max_v, voltage))

        if minute_index < startup_minutes:
            startup_factor = (minute_index + 1) / startup_minutes
            current *= startup_factor
        elif minute_index >= duration_minutes - shutdown_minutes:
            remaining_steps = duration_minutes - minute_index - 1
            shutdown_factor = max(remaining_steps / shutdown_minutes, 0.0)
            current *= shutdown_factor

        if minute_index in anomaly_points:
            # Keep anomaly inside a realistic charging envelope while clearly outside the rolling baseline.
            current = current_max_a + 2.6 + rng.uniform(0.1, 0.45)
            voltage = min(voltage_max_v, voltage_mid + rng.uniform(0.2, 0.45))

        current = max(current, 0.0)

        timestamp = session_start + timedelta(minutes=minute_index)
        payloads.append(
            {
                "device_id": device_code,
                "bien_so_xe": license_plate,
                "current": round(current, 3),
                "voltage": round(voltage, 3),
                "power": round(current * voltage, 3),
                "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
                "meta": {
                    "minute_index": minute_index,
                    "is_statistical_anomaly": minute_index in anomaly_points,
                },
            }
        )

    return payloads


def generate_fake_payload_fleet(
    *,
    duration_minutes: int = 120,
    current_min_a: float = 9.0,
    current_max_a: float = 12.0,
    voltage_min_v: float = 23.0,
    voltage_max_v: float = 25.5,
    start_at: datetime | None = None,
    seed: int | None = None,
) -> list[dict]:
    base_seed = resolve_seed(seed)
    fleet_profiles = [
        {"device_code": "esp32s3_01", "license_plate": "59A-12345", "seed": base_seed + 11, "anomaly_minutes": [32, 79, 104]},
        {"device_code": "esp32s3_02", "license_plate": "51B-67890", "seed": base_seed + 22, "anomaly_minutes": [41, 88]},
        {"device_code": "esp32s3_03", "license_plate": "59A-12345", "seed": base_seed + 33, "anomaly_minutes": [57]},
        {"device_code": "esp32s3_04", "license_plate": "51B-67890", "seed": base_seed + 44, "anomaly_minutes": [66, 111]},
    ]

    fleet_start = start_at or datetime.now(timezone.utc).replace(second=0, microsecond=0)
    payloads = []
    for profile_index, profile in enumerate(fleet_profiles):
        profile_start = fleet_start + timedelta(seconds=profile_index * 10)
        payloads.extend(
            generate_fake_charging_session(
                device_code=profile["device_code"],
                license_plate=profile["license_plate"],
                duration_minutes=duration_minutes,
                current_min_a=current_min_a,
                current_max_a=current_max_a,
                voltage_min_v=voltage_min_v,
                voltage_max_v=voltage_max_v,
                anomaly_minutes=profile["anomaly_minutes"],
                start_at=profile_start,
                seed=profile["seed"],
            )
        )

    payloads.sort(key=lambda payload: (payload["timestamp"], payload["device_id"]))
    return payloads
