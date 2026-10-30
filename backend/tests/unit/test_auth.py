import uuid
from unittest.mock import patch
import pytest
from app.models.user import User


def test_auth_unauthenticated_request_fails(client):
    res = client.get("/me")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHENTICATED"


def test_auth_first_time_citizen_provisioning(client):
    mock_claims = {
        "uid": "new-firebase-citizen-123",
        "phone_number": "+919999900001",
        "name": "Aarav Sharma",
        "aud": "queueless-dev",
    }

    with patch("app.common.dependencies.verify_firebase_id_token", return_value=mock_claims):
        headers = {"Authorization": "Bearer mock-token"}
        res = client.get("/me", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["firebase_uid"] == "new-firebase-citizen-123"
        assert data["phone_number"] == "+919999900001"
        assert data["role"] == "CITIZEN"
        assert data["is_active"] is True


def test_auth_inactive_user_rejected(client, db_session):
    # Pre-create inactive user
    user = User(
        id=uuid.uuid4(),
        firebase_uid="inactive-user-uid",
        role="CITIZEN",
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()

    mock_claims = {
        "uid": "inactive-user-uid",
        "aud": "queueless-dev",
    }

    with patch("app.common.dependencies.verify_firebase_id_token", return_value=mock_claims):
        headers = {"Authorization": "Bearer mock-token"}
        res = client.get("/me", headers=headers)
        assert res.status_code == 403
        assert res.json()["error"]["code"] == "FORBIDDEN"


def test_auth_logout_endpoint(client):
    mock_claims = {
        "uid": "logout-user-uid",
        "phone_number": "+919999900002",
        "aud": "queueless-dev",
    }

    with patch("app.common.dependencies.verify_firebase_id_token", return_value=mock_claims):
        headers = {"Authorization": "Bearer mock-token"}
        # First call provisions
        res_me = client.get("/me", headers=headers)
        assert res_me.status_code == 200

        # Logout
        res_logout = client.post("/auth/logout", headers=headers)
        assert res_logout.status_code == 200
        assert res_logout.json()["status"] == "ok"


def test_auth_wrong_project_rejected(client):
    mock_claims = {
        "uid": "wrong-project-user",
        "aud": "wrong-firebase-project",
    }
    with patch("firebase_admin.auth.verify_id_token", return_value=mock_claims):
        headers = {"Authorization": "Bearer mock-token"}
        res = client.get("/me", headers=headers)
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "UNAUTHENTICATED"


def test_auth_profile_update_cannot_escalate_role(client):
    mock_claims = {
        "uid": "citizen-update-uid",
        "phone_number": "+919999900003",
        "aud": "queueless-dev",
    }
    with patch("app.common.dependencies.verify_firebase_id_token", return_value=mock_claims):
        headers = {"Authorization": "Bearer mock-token"}
        # Provision citizen
        client.get("/me", headers=headers)

        # Attempt to patch name
        patch_res = client.patch("/me", json={"display_name": "Updated Name"}, headers=headers)
        assert patch_res.status_code == 200
        assert patch_res.json()["display_name"] == "Updated Name"
        assert patch_res.json()["role"] == "CITIZEN"

        # Attempt to supply role in body (Pydantic ignores extra attributes)
        patch_res2 = client.patch("/me", json={"role": "OFFICE_ADMIN"}, headers=headers)
        assert patch_res2.status_code == 200
        assert patch_res2.json()["role"] == "CITIZEN"
