from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _engine_options(database_uri: str) -> dict:
    if database_uri.startswith("postgresql+psycopg://"):
        return {
            "pool_pre_ping": True,
            "connect_args": {
                # Supabase transaction pooler does not support psycopg prepared statements.
                "prepare_threshold": None,
            },
        }
    return {}


class Config:
    DEBUG = _as_bool(os.getenv("FLASK_DEBUG") or os.getenv("DEBUG"), default=False)
    TESTING = _as_bool(os.getenv("TESTING"), default=False)
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///mvp.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options(SQLALCHEMY_DATABASE_URI)

    FLASK_RUN_HOST = os.getenv("FLASK_RUN_HOST") or os.getenv("APP_HOST", "127.0.0.1")
    FLASK_RUN_PORT = int(os.getenv("FLASK_RUN_PORT") or os.getenv("APP_PORT") or "5000")
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS") or os.getenv("CORS_ORIGINS", "*")
    CORS_ORIGINS = CORS_ALLOWED_ORIGINS

    MQTT_ENABLED = _as_bool(os.getenv("MQTT_ENABLED"), default=True)
    MQTT_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
    MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
    MQTT_SENSOR_TOPIC = os.getenv("MQTT_SENSOR_TOPIC", "ev/charger/telemetry")
    MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "iot-2026-backend")

    DEFAULT_MIN_CURRENT_MA = int(os.getenv("DEFAULT_MIN_CURRENT_MA", "50"))
    DEFAULT_MAX_CURRENT_MA = int(os.getenv("DEFAULT_MAX_CURRENT_MA", "500"))
    DEFAULT_CHARGING_DETECTION_CURRENT_MA = int(os.getenv("DEFAULT_CHARGING_DETECTION_CURRENT_MA", "50"))
    DEVICE_OFFLINE_SECONDS = int(os.getenv("DEVICE_OFFLINE_SECONDS") or os.getenv("OFFLINE_AFTER_SECONDS") or "60")
    OFFLINE_AFTER_SECONDS = DEVICE_OFFLINE_SECONDS

    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")
