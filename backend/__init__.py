from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify

from backend.config import Config, _engine_options
from backend.extensions import db, jwt, socketio
from backend.routes.admin import admin_bp
from backend.routes.auth import auth_bp
from backend.routes.user import user_bp
from backend.services.alert_service import ensure_system_settings
from backend.services.mqtt_service import init_mqtt
from backend.services.socket_service import init_socketio_handlers


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        static_folder=str(Path(__file__).resolve().parents[1] / "interface"),
        static_url_path="/interface",
    )
    app.config.from_object(Config)

    if config_overrides:
        app.config.update(config_overrides)

    if "SQLALCHEMY_ENGINE_OPTIONS" not in (config_overrides or {}):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = _engine_options(app.config["SQLALCHEMY_DATABASE_URI"])

    register_extensions(app)
    register_middleware(app)
    register_routes(app)
    register_cli(app)

    with app.app_context():
        db.create_all()
        ensure_system_settings()

    init_socketio_handlers()
    init_mqtt(app)

    return app


def register_extensions(app: Flask) -> None:
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(
        app,
        cors_allowed_origins=app.config["CORS_ALLOWED_ORIGINS"],
        async_mode="threading",
    )


def register_middleware(app: Flask) -> None:
    @app.after_request
    def apply_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = app.config["CORS_ALLOWED_ORIGINS"]
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, OPTIONS"
        return response


def register_routes(app: Flask) -> None:
    @app.get("/api/health")
    def healthcheck():
        return jsonify({"status": "ok"})

    @app.route("/api/<path:_path>", methods=["OPTIONS"])
    def preflight(_path: str):
        return ("", 204)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")


def register_cli(app: Flask) -> None:
    from backend.models.entities import User, Vehicle
    from backend.services.alert_service import upsert_system_settings

    @app.cli.command("init-db")
    def init_db_command() -> None:
        db.create_all()
        ensure_system_settings()
        print("Database initialized.")

    @app.cli.command("seed-admin")
    def seed_admin_command() -> None:
        email = app.config["ADMIN_EMAIL"]
        password = app.config["ADMIN_PASSWORD"]
        admin = User.query.filter_by(email=email).first()

        if admin is None:
            admin = User(email=email, role="admin")
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f"Seeded admin user: {email}")
            return

        print(f"Admin already exists: {email}")

    @app.cli.command("sync-settings")
    def sync_settings_command() -> None:
        settings = upsert_system_settings(
            min_current_ma=app.config["DEFAULT_MIN_CURRENT_MA"],
            max_current_ma=app.config["DEFAULT_MAX_CURRENT_MA"],
            updated_by=None,
            charging_detection_current_ma=app.config["DEFAULT_CHARGING_DETECTION_CURRENT_MA"],
        )
        print(
            "Settings synced: "
            f"min_current_ma={settings.min_current_ma}, "
            f"max_current_ma={settings.max_current_ma}, "
            f"charging_detection_current_ma={settings.charging_detection_current_ma}"
        )

    @app.cli.command("seed-dev")
    def seed_dev_command() -> None:
        fixtures = [
            ("admin@example.com", "Admin@123", "admin", []),
            ("user1@example.com", "Password1", "user", ["59A-12345"]),
            ("user2@example.com", "Password1", "user", ["51B-67890"]),
        ]

        for email, password, role, plates in fixtures:
            user = User.query.filter_by(email=email).first()
            if user is None:
                user = User(email=email, role=role)
                user.set_password(password)
                db.session.add(user)
                db.session.flush()

            for plate in plates:
                existing_vehicle = Vehicle.query.filter_by(license_plate=plate).first()
                if existing_vehicle is None:
                    db.session.add(Vehicle(user_id=user.id, license_plate=plate, display_name=plate, is_active=True))

        db.session.commit()
        print("Seeded development users and vehicles.")
