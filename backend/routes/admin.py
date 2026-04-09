from __future__ import annotations

from functools import wraps

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from backend.extensions import db
from backend.models import Alert, Device, DeviceVehicleLink, SensorData, SystemSettings, User, Vehicle
from backend.services.alert_service import derive_device_status

admin_bp = Blueprint("admin", __name__)


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "admin_required"}), 403
        return fn(*args, **kwargs)

    return wrapper


@admin_bp.get("/users")
@admin_required
def users():
    items = [user.to_dict() for user in User.query.order_by(User.email.asc()).all()]
    return jsonify({"items": items})


@admin_bp.get("/devices")
@admin_required
def devices():
    settings = SystemSettings.get_or_create()
    items = []
    for device in Device.query.order_by(Device.device_code.asc()).all():
        latest = (
            SensorData.query.filter_by(device_id=device.id)
            .order_by(SensorData.timestamp.desc())
            .first()
        )
        active_link = (
            DeviceVehicleLink.query.filter_by(device_id=device.id, is_active=True)
            .order_by(DeviceVehicleLink.linked_at.desc())
            .first()
        )
        items.append(
            {
                **device.to_dict(),
                "status": derive_device_status(
                    device=device,
                    reading=latest,
                    settings=settings,
                    offline_after_seconds=current_app.config["DEVICE_OFFLINE_SECONDS"],
                ),
                "latest_reading": latest.to_dict() if latest else None,
                "assigned_vehicle": active_link.vehicle.to_dict() if active_link else None,
                "active_vehicle": latest.vehicle.to_dict() if latest and latest.vehicle else None,
            }
        )

    return jsonify(
        {
            "items": items,
            "summary": {
                "device_count": len(items),
                "alert_count": Alert.query.count(),
            },
        }
    )


@admin_bp.get("/alerts")
@admin_required
def alerts():
    limit = min(int(request.args.get("limit", 100)), 300)
    items = Alert.query.order_by(Alert.created_at.desc()).limit(limit).all()
    return jsonify({"items": [alert.to_dict() for alert in items]})


@admin_bp.get("/history")
@admin_required
def history():
    device_code = (request.args.get("device_code") or "").strip()
    limit = min(int(request.args.get("limit", 200)), 500)
    query = SensorData.query.order_by(SensorData.timestamp.desc())

    if device_code:
        device = Device.query.filter_by(device_code=device_code).first()
        if device is None:
            return jsonify({"error": "device_not_found"}), 404
        query = query.filter(SensorData.device_id == device.id)

    items = query.limit(limit).all()
    return jsonify({"items": [item.to_dict() for item in items]})


@admin_bp.get("/settings")
@admin_required
def get_settings():
    settings = SystemSettings.get_or_create()
    return jsonify(
        {
            "settings": settings.to_dict(),
            **settings.to_dict(),
        }
    )


@admin_bp.put("/settings")
@admin_required
def update_settings():
    data = request.get_json(silent=True) or {}
    min_current = data.get("min_current_ma")
    max_current = data.get("max_current_ma")
    detection_current = data.get("charging_detection_current_ma")

    if min_current is None or max_current is None:
        return jsonify({"error": "min_and_max_required"}), 400

    if float(min_current) >= float(max_current):
        return jsonify({"error": "min_must_be_lower_than_max"}), 400

    settings = SystemSettings.get_or_create()
    if detection_current is None:
        detection_current = min(
            float(max_current),
            max(float(min_current), float(settings.charging_detection_current_ma)),
        )

    if float(detection_current) < float(min_current) or float(detection_current) > float(max_current):
        return jsonify({"error": "detection_must_be_between_min_and_max"}), 400

    settings.min_current_ma = float(min_current)
    settings.max_current_ma = float(max_current)
    settings.charging_detection_current_ma = float(detection_current)
    settings.updated_by = data.get("updated_by")
    db.session.commit()
    return jsonify(
        {
            "settings": settings.to_dict(),
            **settings.to_dict(),
        }
    )


@admin_bp.post("/vehicles/assign")
@admin_required
def assign_vehicle():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    user_email = (data.get("user_email") or "").strip().lower()
    license_plate = (data.get("license_plate") or "").strip().upper()
    display_name = (data.get("display_name") or "").strip() or license_plate
    device_code = (data.get("device_code") or "").strip()

    if (not user_id and not user_email) or not license_plate:
        return jsonify({"error": "user_and_license_plate_required"}), 400

    user = db.session.get(User, int(user_id)) if user_id else User.query.filter_by(email=user_email).first()
    if user is None:
        return jsonify({"error": "user_not_found"}), 404

    vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()
    if vehicle is None:
        vehicle = Vehicle(
            user_id=user.id,
            license_plate=license_plate,
            display_name=display_name,
            is_active=True,
        )
        db.session.add(vehicle)
        db.session.flush()
    else:
        vehicle.user_id = user.id
        vehicle.display_name = display_name
        vehicle.is_active = True

    if device_code:
        device = Device.query.filter_by(device_code=device_code).first()
        if device is None:
            device = Device(device_code=device_code, name=device_code, status="offline")
            db.session.add(device)
            db.session.flush()

        DeviceVehicleLink.query.filter_by(vehicle_id=vehicle.id).update({"is_active": False})
        DeviceVehicleLink.query.filter_by(device_id=device.id).update({"is_active": False})
        db.session.add(DeviceVehicleLink(device_id=device.id, vehicle_id=vehicle.id, is_active=True))

    db.session.commit()
    return jsonify({"vehicle": vehicle.to_dict()})
