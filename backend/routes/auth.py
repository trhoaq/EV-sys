from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from backend.extensions import db
from backend.models import User, Vehicle

auth_bp = Blueprint("auth", __name__)


def _build_response(user: User, access_token: str | None = None) -> dict:
    payload = {
        "user": user.to_dict(),
        "vehicles": [vehicle.to_dict() for vehicle in user.vehicles],
    }
    if access_token is not None:
        payload["access_token"] = access_token
    return payload


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    license_plate = (data.get("license_plate") or "").strip().upper()

    if not email or "@" not in email:
        return jsonify({"error": "A valid email is required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if not license_plate:
        return jsonify({"error": "License plate is required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 409

    if Vehicle.query.filter_by(license_plate=license_plate).first():
        return jsonify({"error": "License plate already exists"}), 409

    user = User(email=email, role="user")
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    db.session.add(
        Vehicle(
            user_id=user.id,
            license_plate=license_plate,
            display_name=license_plate,
            is_active=True,
        )
    )
    db.session.commit()
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(_build_response(user, token)), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(_build_response(user, token))


@auth_bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        return jsonify({"error": "user_not_found"}), 404
    return jsonify(_build_response(user))
