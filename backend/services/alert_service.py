from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import current_app
from sqlalchemy import inspect, text

from backend.extensions import db
from backend.models.entities import Alert, SystemSetting


def ensure_system_settings_schema() -> None:
    inspector = inspect(db.engine)
    if not inspector.has_table("system_settings"):
        return

    columns = {column["name"] for column in inspector.get_columns("system_settings")}
    if "charging_detection_current_ma" in columns:
        return

    default_value = current_app.config["DEFAULT_CHARGING_DETECTION_CURRENT_MA"]
    db.session.execute(text("ALTER TABLE system_settings ADD COLUMN charging_detection_current_ma FLOAT"))
    db.session.execute(
        text(
            "UPDATE system_settings "
            "SET charging_detection_current_ma = :default_value "
            "WHERE charging_detection_current_ma IS NULL"
        ),
        {"default_value": default_value},
    )
    db.session.commit()


def ensure_system_settings() -> SystemSetting:
    ensure_system_settings_schema()
    settings = SystemSetting.query.first()
    if settings is None:
        settings = SystemSetting(
            min_current_ma=current_app.config["DEFAULT_MIN_CURRENT_MA"],
            max_current_ma=current_app.config["DEFAULT_MAX_CURRENT_MA"],
            charging_detection_current_ma=current_app.config["DEFAULT_CHARGING_DETECTION_CURRENT_MA"],
        )
        db.session.add(settings)
        db.session.commit()
    return settings


def get_system_settings() -> SystemSetting:
    return ensure_system_settings()


def upsert_system_settings(
    min_current_ma: float,
    max_current_ma: float,
    updated_by: int | None,
    charging_detection_current_ma: float | None = None,
) -> SystemSetting:
    settings = ensure_system_settings()
    settings.min_current_ma = min_current_ma
    settings.max_current_ma = max_current_ma
    if charging_detection_current_ma is not None:
        settings.charging_detection_current_ma = charging_detection_current_ma
    settings.updated_by = updated_by
    db.session.commit()
    return settings


def classify_current(current: float, settings: SystemSetting) -> tuple[str, str | None, str | None, float | None]:
    if current < settings.min_current_ma:
        return (
            "not_charging",
            "low_current",
            f"Current below minimum threshold ({current} < {settings.min_current_ma})",
            settings.min_current_ma,
        )

    if current > settings.max_current_ma:
        return (
            "abnormal",
            "high_current",
            f"Current above maximum threshold ({current} > {settings.max_current_ma})",
            settings.max_current_ma,
        )

    if current < settings.charging_detection_current_ma:
        return ("not_charging", None, None, None)

    return ("charging", None, None, None)


def create_alert(
    *,
    device_id: int,
    vehicle_id: int | None,
    alert_type: str,
    message: str,
    threshold_value: float,
    measured_value: float,
) -> Alert:
    alert = Alert(
        device_id=device_id,
        vehicle_id=vehicle_id,
        type=alert_type,
        message=message,
        threshold_value=threshold_value,
        measured_value=measured_value,
    )
    db.session.add(alert)
    return alert


def classify_reading(current: float, min_current_ma: float, max_current_ma: float) -> str:
    if current < min_current_ma:
        return "not_charging"
    if current > max_current_ma:
        return "abnormal"
    return "charging"


def build_alert(current: float, min_current_ma: float, max_current_ma: float) -> dict | None:
    if current < min_current_ma:
        return {
            "type": "low_current",
            "message": f"Current below minimum threshold ({current} < {min_current_ma})",
            "threshold_value": min_current_ma,
            "measured_value": current,
        }
    if current > max_current_ma:
        return {
            "type": "high_current",
            "message": f"Current above maximum threshold ({current} > {max_current_ma})",
            "threshold_value": max_current_ma,
            "measured_value": current,
        }
    return None


def derive_device_status(*, device, reading, settings, offline_after_seconds: int) -> str:
    if device is None or device.last_seen_at is None:
        return "offline"

    now = datetime.now(timezone.utc)
    if device.last_seen_at < now - timedelta(seconds=offline_after_seconds):
        return "offline"

    if reading is None:
        return device.status or "online"

    return classify_reading(reading.current, settings.min_current_ma, settings.max_current_ma)
