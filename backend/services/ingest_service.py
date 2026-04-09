from __future__ import annotations

from backend.extensions import db
from backend.models.entities import Device, DeviceVehicleLink, SensorData, Vehicle
from backend.schemas.payloads import validate_sensor_payload
from backend.services.alert_service import classify_current, create_alert, get_system_settings
from backend.services.socket_service import emit_alert, emit_sensor_update


def ingest_sensor_payload(payload: dict) -> dict:
    normalized = validate_sensor_payload(payload)

    device = Device.query.filter_by(device_code=normalized["device_code"]).first()
    if device is None:
        device = Device(device_code=normalized["device_code"], name=normalized["device_code"])
        db.session.add(device)
        db.session.flush()

    settings = get_system_settings()
    raw_vehicle = None
    if normalized["license_plate"]:
        raw_vehicle = Vehicle.query.filter_by(license_plate=normalized["license_plate"]).first()
    should_associate_vehicle = raw_vehicle is not None and normalized["current"] >= settings.charging_detection_current_ma
    vehicle = raw_vehicle if should_associate_vehicle else None

    device.last_seen_at = normalized["timestamp"]
    status, alert_type, alert_message, threshold = classify_current(normalized["current"], settings)
    device.status = status

    if vehicle is not None:
        active_link = DeviceVehicleLink.query.filter_by(
            device_id=device.id,
            vehicle_id=vehicle.id,
            is_active=True,
        ).first()
        if active_link is None:
            DeviceVehicleLink.query.filter_by(device_id=device.id).update({"is_active": False})
            DeviceVehicleLink.query.filter_by(vehicle_id=vehicle.id).update({"is_active": False})
            db.session.add(DeviceVehicleLink(device_id=device.id, vehicle_id=vehicle.id, is_active=True))

    reading = SensorData(
        device_id=device.id,
        vehicle_id=vehicle.id if vehicle else None,
        current=normalized["current"],
        voltage=normalized["voltage"],
        power=normalized["power"],
        raw_payload=normalized["raw_payload"],
        timestamp=normalized["timestamp"],
    )
    db.session.add(reading)

    created_alert = None
    if alert_type and alert_message and threshold is not None:
        created_alert = create_alert(
            device_id=device.id,
            vehicle_id=vehicle.id if vehicle else None,
            alert_type=alert_type,
            message=alert_message,
            threshold_value=threshold,
            measured_value=normalized["current"],
        )

    db.session.commit()

    emit_sensor_update(device=device, vehicle=vehicle, reading=reading)
    if created_alert is not None:
        emit_alert(alert=created_alert, vehicle=vehicle)

    return {
        "device": device.to_dict(),
        "vehicle": vehicle.to_dict() if vehicle else None,
        "reading": reading.to_dict(),
        "alert": created_alert.to_dict() if created_alert else None,
    }
