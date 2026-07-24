"""
Tests for the Setup API — Sprint 3.2 First-Time Setup & Bootstrap Wizard.

Covers:
  - Fresh install detection
  - Existing installation detection
  - Bootstrap success
  - Duplicate bootstrap rejection
  - Password validation (mismatch, too short)
  - Email uniqueness
  - Company/site name uniqueness
  - Transaction rollback on failure
  - Setup status endpoint
  - API permissions (no auth required for setup endpoints)
"""

import pytest

from app.models.db.company import Company
from app.models.db.site import Site
from app.models.db.user import User
from app.services.auth_service import hash_password
from app.services.setup_service import is_setup_required


# ── Fixtures ──────────────────────────────────────────────────────


def _valid_payload(**overrides):
    base = {
        "company_name": "Acme Corp",
        "company_code": "ACME",
        "site_name": "Headquarters",
        "site_timezone": "UTC",
        "admin_display_name": "Admin User",
        "admin_email": "admin@acme.com",
        "admin_password": "securepass123",
        "admin_confirm_password": "securepass123",
    }
    base.update(overrides)
    return base


# ── Setup Status ──────────────────────────────────────────────────


class TestSetupStatus:
    def test_setup_required_when_no_users(self, client):
        resp = client.get("/api/v1/setup/status")
        assert resp.status_code == 200
        assert resp.json()["setup_required"] is True

    def test_setup_not_required_when_users_exist(self, client, db_session):
        user = User(
            email="existing@test.com",
            display_name="Existing",
            password_hash=hash_password("pass12345"),
            role="global_admin",
        )
        db_session.add(user)
        db_session.commit()

        resp = client.get("/api/v1/setup/status")
        assert resp.status_code == 200
        assert resp.json()["setup_required"] is False

    def test_setup_status_works_without_real_token(self, client, db_session):
        """Setup status endpoint doesn't require auth."""
        resp = client.get("/api/v1/setup/status")
        assert resp.status_code == 200


# ── Bootstrap Success ─────────────────────────────────────────────


class TestBootstrap:
    def test_bootstrap_creates_company_site_admin(self, client, db_session):
        resp = client.post(
            "/api/v1/setup/bootstrap",
            json=_valid_payload(),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["company_id"] > 0
        assert body["site_id"] > 0
        assert body["admin_id"] > 0
        assert "complete" in body["message"].lower()

    def test_bootstrap_creates_valid_records(self, client, db_session):
        client.post("/api/v1/setup/bootstrap", json=_valid_payload())

        company = db_session.get(Company, 1)
        assert company is not None
        assert company.name == "Acme Corp"
        assert company.status == "active"
        assert company.enabled is True
        assert company.uuid  # auto-generated UUID

        site = db_session.get(Site, 1)
        assert site is not None
        assert site.name == "Headquarters"
        assert site.code == "headquarters"
        assert site.is_default is True
        assert site.company_id == company.id

        admin = db_session.get(User, 1)
        assert admin is not None
        assert admin.email == "admin@acme.com"
        assert admin.role == "global_admin"
        assert admin.company_id == company.id
        assert admin.site_id == site.id
        assert admin.enabled is True
        assert admin.password_hash != "securepass123"

    def test_bootstrap_optional_fields(self, client, db_session):
        resp = client.post(
            "/api/v1/setup/bootstrap",
            json=_valid_payload(company_code="", site_timezone=""),
        )
        assert resp.status_code == 201

    def test_setup_disabled_after_bootstrap(self, client, db_session):
        client.post("/api/v1/setup/bootstrap", json=_valid_payload())

        resp = client.get("/api/v1/setup/status")
        assert resp.json()["setup_required"] is False

    def test_bootstrap_works_without_real_token(self, client, db_session):
        """Bootstrap endpoint doesn't require auth — the mock auth passes but
        setup_service doesn't check the user, just the user count."""
        resp = client.post(
            "/api/v1/setup/bootstrap",
            json=_valid_payload(),
        )
        assert resp.status_code == 201


# ── Duplicate Bootstrap Rejection ─────────────────────────────────


class TestDuplicateBootstrap:
    def test_second_bootstrap_rejected(self, client, db_session):
        client.post("/api/v1/setup/bootstrap", json=_valid_payload())

        resp = client.post(
            "/api/v1/setup/bootstrap",
            json=_valid_payload(),
        )
        assert resp.status_code in (403, 409)

    def test_bootstrap_after_existing_user_returns_403(self, client, db_session):
        user = User(
            email="existing@test.com",
            display_name="Existing",
            password_hash=hash_password("pass12345"),
            role="global_admin",
        )
        db_session.add(user)
        db_session.commit()

        resp = client.post(
            "/api/v1/setup/bootstrap",
            json=_valid_payload(),
        )
        assert resp.status_code == 403


# ── Validation ────────────────────────────────────────────────────


class TestValidation:
    def test_password_mismatch(self, client, db_session):
        resp = client.post(
            "/api/v1/setup/bootstrap",
            json=_valid_payload(
                admin_password="securepass123",
                admin_confirm_password="differentpass",
            ),
        )
        assert resp.status_code == 400
        assert "do not match" in resp.json()["detail"].lower()

    def test_password_too_short(self, client, db_session):
        resp = client.post(
            "/api/v1/setup/bootstrap",
            json=_valid_payload(
                admin_password="short",
                admin_confirm_password="short",
            ),
        )
        assert resp.status_code == 422

    def test_duplicate_email(self, client, db_session):
        user = User(
            email="admin@acme.com",
            display_name="Existing",
            password_hash=hash_password("pass12345"),
            role="global_admin",
        )
        db_session.add(user)
        db_session.commit()

        resp = client.post(
            "/api/v1/setup/bootstrap",
            json=_valid_payload(),
        )
        assert resp.status_code == 409
        assert "email" in resp.json()["detail"].lower()

    def test_duplicate_company_name(self, client, db_session):
        company = Company(
            uuid="existing-uuid",
            name="Acme Corp",
            display_name="Acme Corp",
            status="active",
            enabled=True,
            is_global=False,
        )
        db_session.add(company)
        db_session.commit()

        resp = client.post(
            "/api/v1/setup/bootstrap",
            json=_valid_payload(),
        )
        assert resp.status_code == 409
        assert "company" in resp.json()["detail"].lower()

    def test_duplicate_site_name(self, client, db_session):
        site = Site(
            name="Headquarters",
            code="headquarters",
            enabled=True,
            is_default=True,
        )
        db_session.add(site)
        db_session.commit()

        resp = client.post(
            "/api/v1/setup/bootstrap",
            json=_valid_payload(),
        )
        assert resp.status_code == 409
        assert "site" in resp.json()["detail"].lower()

    def test_missing_company_name(self, client, db_session):
        resp = client.post(
            "/api/v1/setup/bootstrap",
            json=_valid_payload(company_name=""),
        )
        assert resp.status_code == 422

    def test_missing_admin_email(self, client, db_session):
        resp = client.post(
            "/api/v1/setup/bootstrap",
            json=_valid_payload(admin_email=""),
        )
        assert resp.status_code == 422

    def test_invalid_email_format(self, client, db_session):
        resp = client.post(
            "/api/v1/setup/bootstrap",
            json=_valid_payload(admin_email="not-an-email"),
        )
        assert resp.status_code == 422


# ── Transaction Safety ────────────────────────────────────────────


class TestTransactionSafety:
    def test_no_partial_records_on_failure(self, client, db_session):
        """When bootstrap fails, no records should remain."""
        resp = client.post(
            "/api/v1/setup/bootstrap",
            json=_valid_payload(
                admin_password="short",
                admin_confirm_password="short",
            ),
        )
        assert resp.status_code in (400, 422)

        assert db_session.query(Company).count() == 0
        assert db_session.query(Site).count() == 0
        assert db_session.query(User).count() == 0


# ── Password Security ─────────────────────────────────────────────


class TestPasswordSecurity:
    def test_password_not_stored_in_plaintext(self, client, db_session):
        client.post("/api/v1/setup/bootstrap", json=_valid_payload())

        admin = db_session.query(User).first()
        assert admin is not None
        assert admin.password_hash != "securepass123"
        assert "$" in admin.password_hash

    def test_password_is_verifiable(self, client, db_session):
        client.post("/api/v1/setup/bootstrap", json=_valid_payload())

        from app.services.auth_service import verify_password

        admin = db_session.query(User).first()
        assert verify_password("securepass123", admin.password_hash)
        assert not verify_password("wrongpassword", admin.password_hash)


# ── is_setup_required() Unit Tests ────────────────────────────────


class TestIsSetupRequired:
    def test_returns_true_for_empty_db(self, db_session):
        assert is_setup_required(db_session) is True

    def test_returns_false_after_user_created(self, db_session):
        user = User(
            email="test@test.com",
            display_name="Test",
            password_hash=hash_password("pass12345"),
            role="global_admin",
        )
        db_session.add(user)
        db_session.commit()
        assert is_setup_required(db_session) is False


# ── Full Login Flow ───────────────────────────────────────────────


class TestLoginAfterBootstrap:
    def test_can_login_with_bootstrap_credentials(self, client, db_session):
        client.post("/api/v1/setup/bootstrap", json=_valid_payload())

        resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@acme.com",
                "password": "securepass123",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"]
        assert body["user"]["email"] == "admin@acme.com"
        assert body["user"]["role"] == "global_admin"
