from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from backend.extensions import db
from backend.models import Alert, SensorData, SystemSettings, User, Vehicle
from backend.services.alert_service import derive_device_status

user_bp = Blueprint("user", __name__)


def _current_user() -> User:
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        raise LookupError("user_not_found")
    return user


def _ensure_user_access(plate: str) -> Vehicle:
    vehicle = Vehicle.query.filter_by(license_plate=plate.upper(), is_active=True).first()
    if vehicle is None:
        raise LookupError("vehicle_not_found")

    claims = get_jwt()
    user = _current_user()
    if claims.get("role") != "admin" and vehicle.user_id != user.id:
        raise PermissionError("forbidden")
    return vehicle


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@user_bp.get("/dashboard")
@jwt_required()
def dashboard():
    user = _current_user()
    settings = SystemSettings.get_or_create()
    vehicles = Vehicle.query.order_by(Vehicle.license_plate.asc()).all() if user.role == "admin" else user.vehicles

    vehicles_payload = []
    for vehicle in vehicles:
        latest = (
            SensorData.query.filter_by(vehicle_id=vehicle.id)
            .order_by(SensorData.timestamp.desc())
            .first()
        )
        latest_alert = (
            Alert.query.filter_by(vehicle_id=vehicle.id).order_by(Alert.created_at.desc()).first()
        )
        device = latest.device if latest else None
        status = derive_device_status(
            device=device,
            reading=latest,
            settings=settings,
            offline_after_seconds=current_app.config["DEVICE_OFFLINE_SECONDS"],
        )
        vehicle_payload = {
            **vehicle.to_dict(),
            "latest_reading": latest.to_dict() if latest else None,
            "latest_alert": latest_alert.to_dict() if latest_alert else None,
            "status": status,
        }
        vehicles_payload.append(vehicle_payload)

    alert_count = (
        Alert.query.join(Vehicle, Alert.vehicle_id == Vehicle.id)
        .filter(Vehicle.user_id == user.id)
        .count()
        if user.role != "admin"
        else Alert.query.count()
    )

    return jsonify(
        {
            "settings": settings.to_dict(),
            "vehicles": vehicles_payload,
            "summary": {"alert_count": alert_count},
            "user": user.to_dict(),
        }
    )


@user_bp.get("/history")
@jwt_required()
def history():
    plate = (request.args.get("plate") or "").strip().upper()
    limit = min(int(request.args.get("limit", 200)), 500)
    settings = SystemSettings.get_or_create()
    query = SensorData.query.order_by(SensorData.timestamp.desc())
    query = query.filter(SensorData.current >= settings.charging_detection_current_ma)

    if plate:
        try:
            vehicle = _ensure_user_access(plate)
        except LookupError:
            return jsonify({"error": "vehicle_not_found"}), 404
        except PermissionError:
            return jsonify({"error": "forbidden"}), 403
        query = query.filter(SensorData.vehicle_id == vehicle.id)
    elif get_jwt().get("role") != "admin":
        user = _current_user()
        vehicle_ids = [vehicle.id for vehicle in user.vehicles]
        if vehicle_ids:
            query = query.filter(SensorData.vehicle_id.in_(vehicle_ids))
        else:
            query = query.filter(SensorData.id == -1)

    from_value = request.args.get("from")
    to_value = request.args.get("to")

    if from_value:
        query = query.filter(SensorData.timestamp >= _parse_timestamp(from_value))
    if to_value:
        query = query.filter(SensorData.timestamp <= _parse_timestamp(to_value))

    readings = query.limit(limit).all()
    return jsonify({"items": [reading.to_dict() for reading in readings]})


@user_bp.get("/alerts")
@jwt_required()
def alerts():
    limit = min(int(request.args.get("limit", 50)), 200)
    query = Alert.query.order_by(Alert.created_at.desc())

    if get_jwt().get("role") != "admin":
        user = _current_user()
        vehicle_ids = [vehicle.id for vehicle in user.vehicles]
        if vehicle_ids:
            query = query.filter(Alert.vehicle_id.in_(vehicle_ids))
        else:
            query = query.filter(Alert.id == -1)

    items = query.limit(limit).all()
    return jsonify({"items": [alert.to_dict() for alert in items]})
