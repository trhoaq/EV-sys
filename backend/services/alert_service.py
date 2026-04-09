from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import median

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


def detect_statistical_current_anomaly(
    *,
    current: float,
    history: list[float],
    min_samples: int,
    z_threshold: float,
    relative_delta_threshold: float,
) -> dict | None:
    clean_history = [float(value) for value in history if value is not None]
    if len(clean_history) < min_samples:
        return None

    baseline = median(clean_history)
    deviations = [abs(value - baseline) for value in clean_history]
    mad = median(deviations)

    if mad > 0:
        robust_z_score = 0.6745 * abs(current - baseline) / mad
        if robust_z_score >= z_threshold:
            return {
                "basis": "robust_z_score",
                "score": robust_z_score,
                "reference_value": baseline,
                "history_size": len(clean_history),
            }
        return None

    relative_delta = abs(current - baseline) / max(abs(baseline), 1.0)
    if relative_delta >= relative_delta_threshold:
        return {
            "basis": "relative_delta",
            "score": relative_delta,
            "reference_value": baseline,
            "history_size": len(clean_history),
        }

    return None


def _threshold_alert_payload(current: float, min_current_ma: float, max_current_ma: float) -> dict | None:
    if current > max_current_ma:
        return {
            "status": "abnormal",
            "type": "high_current",
            "message": f"Current above maximum threshold ({current} > {max_current_ma})",
            "threshold_value": max_current_ma,
        }

    return None


def classify_current(current: float, settings: SystemSetting) -> tuple[str, str | None, str | None, float | None]:
    threshold_alert = _threshold_alert_payload(
        current=current,
        min_current_ma=settings.min_current_ma,
        max_current_ma=settings.max_current_ma,
    )
    if threshold_alert is not None:
        return (
            threshold_alert["status"],
            threshold_alert["type"],
            threshold_alert["message"],
            threshold_alert["threshold_value"],
        )

    if current < max(settings.min_current_ma, settings.charging_detection_current_ma):
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
    threshold_alert = _threshold_alert_payload(current, min_current_ma, max_current_ma)
    if threshold_alert is None:
        return None

    return {
        "type": threshold_alert["type"],
        "message": threshold_alert["message"],
        "threshold_value": threshold_alert["threshold_value"],
        "measured_value": current,
    }


def derive_device_status(*, device, reading, settings, offline_after_seconds: int) -> str:
    if device is None or device.last_seen_at is None:
        return "offline"

    now = datetime.now(timezone.utc)
    last_seen_at = device.last_seen_at
    if last_seen_at.tzinfo is None:
        last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)

    if last_seen_at < now - timedelta(seconds=offline_after_seconds):
        return "offline"

    return device.status or "online"
