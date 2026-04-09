from __future__ import annotations


def test_user_cannot_access_other_vehicle_history(client, auth_tokens):
    response = client.get(
        "/api/user/history?plate=51B-67890",
        headers={"Authorization": f"Bearer {auth_tokens['user1']}"},
    )

    assert response.status_code == 403


def test_admin_can_update_global_settings(client, auth_tokens):
    response = client.put(
        "/api/admin/settings",
        json={"min_current_ma": 60, "max_current_ma": 400},
        headers={"Authorization": f"Bearer {auth_tokens['admin']}"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["min_current_ma"] == 60
    assert body["max_current_ma"] == 400
