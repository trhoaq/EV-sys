from __future__ import annotations


def test_register_and_login_flow(client):
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "fresh@example.com",
            "password": "Password1",
            "license_plate": "60A-12345",
        },
    )
    assert register_response.status_code == 201
    assert register_response.get_json()["user"]["email"] == "fresh@example.com"
    assert register_response.get_json()["vehicles"][0]["license_plate"] == "60A-12345"

    login_response = client.post(
        "/api/auth/login",
        json={"email": "fresh@example.com", "password": "Password1"},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.get_json()


def test_register_requires_license_plate(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "no-plate@example.com", "password": "Password1"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "License plate is required"


def test_register_rejects_duplicate_license_plate(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "duplicate-plate@example.com",
            "password": "Password1",
            "license_plate": "59A-12345",
        },
    )

    assert response.status_code == 409
    assert response.get_json()["error"] == "License plate already exists"


def test_me_returns_profile(client, auth_tokens):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {auth_tokens['user1']}"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["user"]["email"] == "user1@example.com"
    assert body["vehicles"][0]["license_plate"] == "59A-12345"
