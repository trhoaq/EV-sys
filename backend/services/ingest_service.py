from __future__ import annotations

from flask import current_app

from backend.extensions import db
from backend.models.entities import Device, DeviceVehicleLink, SensorData, Vehicle
from backend.schemas.payloads import validate_sensor_payload
from backend.services.alert_service import (
    classify_current,
    create_alert,
    detect_statistical_current_anomaly,
    get_system_settings,
)
from backend.services.charging_session_service import close_session, get_active_session, start_session, update_session_sample
from backend.services.socket_service import emit_alert, emit_sensor_update


def ingest_sensor_payload(
    payload: dict,
    *,
    use_payload_timestamp: bool = False,
    emit_events: bool = True,
) -> dict:
    normalized = validate_sensor_payload(payload, use_payload_timestamp=use_payload_timestamp)

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

    baseline_values = []
    if normalized["current"] >= settings.charging_detection_current_ma:
        baseline_values = [
            sample.current
            for sample in (
                SensorData.query.filter_by(device_id=device.id)
                .filter(SensorData.current >= settings.charging_detection_current_ma)
                .order_by(SensorData.timestamp.desc())
                .limit(current_app.config["STAT_CURRENT_WINDOW_SIZE"])
                .all()
            )
        ]

    statistical_anomaly = detect_statistical_current_anomaly(
        current=normalized["current"],
        history=baseline_values,
        min_samples=current_app.config["STAT_CURRENT_MIN_SAMPLES"],
        z_threshold=current_app.config["STAT_CURRENT_Z_THRESHOLD"],
        relative_delta_threshold=current_app.config["STAT_CURRENT_RELATIVE_DELTA"],
    )
    if statistical_anomaly is not None and alert_type is None:
        status = "abnormal"
        alert_type = "statistical_current_anomaly"
        alert_message = (
            "Current deviates from rolling baseline "
            f"({statistical_anomaly['basis']}={statistical_anomaly['score']:.2f}, "
            f"median={statistical_anomaly['reference_value']:.1f} mA)"
        )
        threshold = statistical_anomaly["reference_value"]

    device.status = status

    active_session = get_active_session(device.id)
    if vehicle is not None:
        if active_session is None:
            start_session(
                device_id=device.id,
                vehicle_id=vehicle.id,
                started_at=normalized["timestamp"],
                power_w=normalized["power"],
                rate_vnd_per_kwh=current_app.config["PRICE_PER_KWH_VND"],
            )
        elif active_session.vehicle_id == vehicle.id:
            update_session_sample(
                active_session,
                sample_at=normalized["timestamp"],
                power_w=normalized["power"],
            )
        else:
            close_session(
                active_session,
                ended_at=normalized["timestamp"],
                final_power_w=0.0,
            )
            start_session(
                device_id=device.id,
                vehicle_id=vehicle.id,
                started_at=normalized["timestamp"],
                power_w=normalized["power"],
                rate_vnd_per_kwh=current_app.config["PRICE_PER_KWH_VND"],
            )
    elif active_session is not None:
        close_session(
            active_session,
            ended_at=normalized["timestamp"],
            final_power_w=max(normalized["power"], 0.0),
        )

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

    if emit_events:
        emit_sensor_update(device=device, vehicle=vehicle, reading=reading)
        if created_alert is not None:
            emit_alert(alert=created_alert, vehicle=vehicle)

    return {
        "device": device.to_dict(),
        "vehicle": vehicle.to_dict() if vehicle else None,
        "reading": reading.to_dict(),
        "alert": created_alert.to_dict() if created_alert else None,
    }
