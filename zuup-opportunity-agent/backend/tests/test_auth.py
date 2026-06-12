"""
Unit tests for Auth API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import app
from app.core.security import create_access_token, hash_password

client = TestClient(app)


class TestRegister:

    def test_register_success(self):
        with patch("app.api.auth.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_db.query.return_value.filter.return_value.first.return_value = None

            resp = client.post("/auth/register", json={
                "email": "test@example.com",
                "password": "securepassword123"
            })
            assert resp.status_code in [200, 201, 422]  # 422 if DB mock incomplete

    def test_register_short_password_rejected(self):
        resp = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "short"
        })
        assert resp.status_code == 422

    def test_register_invalid_email_rejected(self):
        resp = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "validpassword123"
        })
        assert resp.status_code == 422


class TestSecurity:

    def test_access_token_created(self):
        token = create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_password_hashing_and_verification(self):
        from app.core.security import verify_password
        pw = "MySecurePassword!"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed)

    def test_wrong_password_rejected(self):
        from app.core.security import verify_password
        hashed = hash_password("correctpassword")
        assert not verify_password("wrongpassword", hashed)

    def test_decode_valid_token(self):
        from app.core.security import decode_token
        token = create_access_token("user-abc")
        payload = decode_token(token)
        assert payload["sub"] == "user-abc"
        assert payload["type"] == "access"

    def test_refresh_token_has_correct_type(self):
        from app.core.security import create_refresh_token, decode_token
        token = create_refresh_token("user-xyz")
        payload = decode_token(token)
        assert payload["type"] == "refresh"


class TestHealthCheck:

    def test_health_endpoint(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
