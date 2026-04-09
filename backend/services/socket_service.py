from __future__ import annotations

from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import emit, join_room

from backend.extensions import socketio

_handlers_registered = False


def init_socketio_handlers() -> None:
    global _handlers_registered

    if _handlers_registered:
        return

    @socketio.on("connect")
    def handle_connect(auth=None):
        token = request.args.get("token")
        if auth and not token:
            token = auth.get("token")

        if not token:
            return False

        try:
            decoded = decode_token(token)
        except Exception:
            return False

        user_id = decoded["sub"]
        role = decoded.get("role")
        join_room(f"user:{user_id}")
        if role == "admin":
            join_room("admins")

        emit("connected", {"user_id": user_id, "role": role})

    _handlers_registered = True


def emit_sensor_update(*, device, vehicle, reading) -> None:
    payload = {
        "device": device.to_dict(),
        "vehicle": vehicle.to_dict() if vehicle else None,
        "reading": reading.to_dict(),
    }

    socketio.emit("sensor:update:admin", payload, to="admins")
    socketio.emit("device:status", payload["device"], to="admins")

    if vehicle is not None:
        socketio.emit("sensor:update:user", payload, to=f"user:{vehicle.user_id}")


def emit_alert(*, alert, vehicle) -> None:
    payload = alert.to_dict()
    socketio.emit("alert:new", payload, to="admins")

    if vehicle is not None:
        socketio.emit("alert:new", payload, to=f"user:{vehicle.user_id}")
