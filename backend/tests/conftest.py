from __future__ import annotations

from pathlib import Path

import pytest

from backend import create_app
from backend.extensions import db
from backend.models.entities import User, Vehicle
from backend.services.alert_service import upsert_system_settings


@pytest.fixture()
def app(tmp_path: Path):
    database_path = tmp_path / "test.db"
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
            "MQTT_ENABLED": False,
            "JWT_SECRET_KEY": "test-secret-key-with-32-plus-bytes",
        }
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        upsert_system_settings(50, 500, None)

        admin = User(email="admin@example.com", role="admin")
        admin.set_password("Admin@123")
        user1 = User(email="user1@example.com", role="user")
        user1.set_password("123456")
        user2 = User(email="user2@example.com", role="user")
        user2.set_password("123456")
        db.session.add_all([admin, user1, user2])
        db.session.flush()

        db.session.add_all(
            [
                Vehicle(user_id=user1.id, license_plate="59A-12345"),
                Vehicle(user_id=user2.id, license_plate="51B-67890"),
            ]
        )
        db.session.commit()

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_tokens(client):
    def _login(email: str, password: str) -> str:
        response = client.post("/api/auth/login", json={"email": email, "password": password})
        body = response.get_json()
        return body["access_token"]

    return {
        "admin": _login("admin@example.com", "Admin@123"),
        "user1": _login("user1@example.com", "123456"),
        "user2": _login("user2@example.com", "123456"),
    }


@pytest.fixture()
def admin_token(auth_tokens):
    return auth_tokens["admin"]


@pytest.fixture()
def user1_token(auth_tokens):
    return auth_tokens["user1"]


@pytest.fixture()
def user2_token(auth_tokens):
    return auth_tokens["user2"]
