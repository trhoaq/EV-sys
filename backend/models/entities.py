from __future__ import annotations

from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from backend.extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="user")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    vehicles = db.relationship("Vehicle", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "vehicles": [vehicle.to_dict() for vehicle in self.vehicles],
        }


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    license_plate = db.Column(db.String(32), unique=True, nullable=False)
    display_name = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    user = db.relationship("User", back_populates="vehicles")
    links = db.relationship("DeviceVehicleLink", back_populates="vehicle", cascade="all, delete-orphan")
    sensor_data = db.relationship("SensorData", back_populates="vehicle")
    alerts = db.relationship("Alert", back_populates="vehicle")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "license_plate": self.license_plate,
            "display_name": self.display_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    device_code = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(32), nullable=False, default="offline")
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    links = db.relationship("DeviceVehicleLink", back_populates="device", cascade="all, delete-orphan")
    sensor_data = db.relationship("SensorData", back_populates="device")
    alerts = db.relationship("Alert", back_populates="device")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_code": self.device_code,
            "name": self.name,
            "status": self.status,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DeviceVehicleLink(db.Model):
    __tablename__ = "device_vehicle_links"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    linked_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    device = db.relationship("Device", back_populates="links")
    vehicle = db.relationship("Vehicle", back_populates="links")


class SensorData(db.Model):
    __tablename__ = "sensor_data"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=True)
    current = db.Column(db.Float, nullable=False)
    voltage = db.Column(db.Float, nullable=False)
    power = db.Column(db.Float, nullable=False)
    raw_payload = db.Column(db.JSON, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False)

    device = db.relationship("Device", back_populates="sensor_data")
    vehicle = db.relationship("Vehicle", back_populates="sensor_data")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_id": self.device_id,
            "vehicle_id": self.vehicle_id,
            "current": self.current,
            "voltage": self.voltage,
            "power": self.power,
            "status": self.device.status if self.device else None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "license_plate": self.vehicle.license_plate if self.vehicle else None,
            "device_code": self.device.device_code if self.device else None,
        }


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=True)
    type = db.Column(db.String(64), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    threshold_value = db.Column(db.Float, nullable=False)
    measured_value = db.Column(db.Float, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    device = db.relationship("Device", back_populates="alerts")
    vehicle = db.relationship("Vehicle", back_populates="alerts")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_id": self.device_id,
            "vehicle_id": self.vehicle_id,
            "type": self.type,
            "message": self.message,
            "threshold_value": self.threshold_value,
            "measured_value": self.measured_value,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ChargingSession(db.Model):
    __tablename__ = "charging_sessions"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False, index=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False, index=True)
    status = db.Column(db.String(32), nullable=False, default="active", index=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False)
    ended_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_sample_at = db.Column(db.DateTime(timezone=True), nullable=False)
    last_power_w = db.Column(db.Float, nullable=False, default=0.0)
    reading_count = db.Column(db.Integer, nullable=False, default=1)
    energy_kwh = db.Column(db.Float, nullable=False, default=0.0)
    rate_vnd_per_kwh = db.Column(db.Integer, nullable=False, default=2500)
    total_vnd = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    device = db.relationship("Device", lazy="joined")
    vehicle = db.relationship("Vehicle", lazy="joined")

    def to_dict(self) -> dict:
        duration_minutes = None
        if self.ended_at is not None:
            start = self.started_at if self.started_at.tzinfo is not None else self.started_at.replace(tzinfo=timezone.utc)
            end = self.ended_at if self.ended_at.tzinfo is not None else self.ended_at.replace(tzinfo=timezone.utc)
            duration_minutes = round((end - start).total_seconds() / 60, 2)

        return {
            "id": self.id,
            "device_id": self.device_id,
            "vehicle_id": self.vehicle_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "reading_count": self.reading_count,
            "energy_kwh": round(self.energy_kwh, 6),
            "rate_vnd_per_kwh": self.rate_vnd_per_kwh,
            "total_vnd": self.total_vnd,
            "duration_minutes": duration_minutes,
            "device_code": self.device.device_code if self.device else None,
            "license_plate": self.vehicle.license_plate if self.vehicle else None,
        }


class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)
    min_current_ma = db.Column(db.Float, nullable=False, default=50)
    max_current_ma = db.Column(db.Float, nullable=False, default=500)
    charging_detection_current_ma = db.Column(db.Float, nullable=False, default=50)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "min_current_ma": self.min_current_ma,
            "max_current_ma": self.max_current_ma,
            "charging_detection_current_ma": self.charging_detection_current_ma,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_or_create(cls) -> "SystemSetting":
        settings = cls.query.first()
        if settings is None:
            from flask import current_app

            settings = cls(
                min_current_ma=current_app.config["DEFAULT_MIN_CURRENT_MA"],
                max_current_ma=current_app.config["DEFAULT_MAX_CURRENT_MA"],
                charging_detection_current_ma=current_app.config["DEFAULT_CHARGING_DETECTION_CURRENT_MA"],
                updated_by=None,
            )
            db.session.add(settings)
            db.session.commit()
        return settings
