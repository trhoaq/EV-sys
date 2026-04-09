from __future__ import annotations

from datetime import datetime, timezone

def validate_sensor_payload(payload: dict) -> dict:
    device_code = (payload.get("device_id") or payload.get("charger_id") or "").strip()
    license_plate = (payload.get("bien_so_xe") or "").strip().upper()

    if not device_code:
        raise ValueError("Missing device_id or charger_id")

    try:
        current = float(payload["current"])
        voltage = float(payload["voltage"])
        power = float(payload["power"])
    except KeyError as exc:
        raise ValueError(f"Missing field: {exc.args[0]}") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError("current, voltage, and power must be numeric") from exc

    timestamp = datetime.now(timezone.utc)
    return {
        "device_code": device_code,
        "license_plate": license_plate or None,
        "current": current,
        "voltage": voltage,
        "power": power,
        "timestamp": timestamp,
        "raw_payload": payload,
    }
