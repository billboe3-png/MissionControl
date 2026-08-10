"""
Startup Configuration Tests

Tests for secret key validation, friendly error messages,
and Docker environment loading.
"""

import os
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet

from app.core.config import get_settings
from app.core.startup_check import validate_all, validate_secret_key

# ------------------------------------------------------------------ #
# validate_secret_key                                                 #
# ------------------------------------------------------------------ #


class TestValidateSecretKey:
    """Tests for the validate_secret_key function."""

    def test_valid_key_returns_key(self):
        """Test that a valid Fernet key is returned as-is."""
        key = Fernet.generate_key().decode()
        with patch.dict(os.environ, {"MISSIONCONTROL_SECRET_KEY": key}):
            result = validate_secret_key()
        assert result == key

    def test_valid_key_with_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        key = Fernet.generate_key().decode()
        padded = f"  {key}  "
        with patch.dict(os.environ, {"MISSIONCONTROL_SECRET_KEY": padded}):
            result = validate_secret_key()
        assert result == key

    def test_missing_key_exits(self):
        """Test that a missing key triggers sys.exit(1)."""
        with patch.dict(os.environ, {}, clear=True), pytest.raises(SystemExit, match="1"):
            validate_secret_key()

    def test_empty_key_exits(self):
        """Test that an empty string key triggers sys.exit(1)."""
        with patch.dict(os.environ, {"MISSIONCONTROL_SECRET_KEY": ""}), pytest.raises(SystemExit, match="1"):
            validate_secret_key()

    def test_whitespace_only_key_exits(self):
        """Test that whitespace-only key triggers sys.exit(1)."""
        with patch.dict(
            os.environ, {"MISSIONCONTROL_SECRET_KEY": "   "}
        ), pytest.raises(SystemExit, match="1"):
            validate_secret_key()

    def test_invalid_key_exits(self):
        """Test that an invalid Fernet key triggers sys.exit(1)."""
        with patch.dict(
            os.environ, {"MISSIONCONTROL_SECRET_KEY": "not-a-valid-key"}
        ), pytest.raises(SystemExit, match="1"):
            validate_secret_key()

    def test_too_short_key_exits(self):
        """Test that a truncated key triggers sys.exit(1)."""
        with patch.dict(
            os.environ, {"MISSIONCONTROL_SECRET_KEY": "abc123"}
        ), pytest.raises(SystemExit, match="1"):
            validate_secret_key()

    def test_error_message_mentions_key_name(self, capsys):
        """Test that the error output mentions MISSIONCONTROL_SECRET_KEY."""
        with patch.dict(os.environ, {}, clear=True), pytest.raises(SystemExit):
            validate_secret_key()
        captured = capsys.readouterr()
        assert "MISSIONCONTROL_SECRET_KEY" in captured.err

    def test_error_message_mentions_fernet(self, capsys):
        """Test that the error output mentions Fernet key generation."""
        with patch.dict(os.environ, {}, clear=True), pytest.raises(SystemExit):
            validate_secret_key()
        captured = capsys.readouterr()
        assert "Fernet" in captured.err

    def test_invalid_key_error_mentions_fernet(self, capsys):
        """Test that invalid key error mentions Fernet key generation."""
        with patch.dict(
            os.environ, {"MISSIONCONTROL_SECRET_KEY": "bad-key-value"}
        ), pytest.raises(SystemExit):
            validate_secret_key()
        captured = capsys.readouterr()
        assert "not a valid Fernet key" in captured.err


# ------------------------------------------------------------------ #
# validate_all                                                        #
# ------------------------------------------------------------------ #


class TestValidateAll:
    """Tests for the validate_all function."""

    def test_valid_returns_dict(self):
        """Test that validate_all returns a dict with secret_key."""
        key = Fernet.generate_key().decode()
        with patch.dict(os.environ, {"MISSIONCONTROL_SECRET_KEY": key}):
            result = validate_all()
        assert isinstance(result, dict)
        assert result["secret_key"] == key

    def test_missing_key_exits(self):
        """Test that validate_all exits when key is missing."""
        with patch.dict(os.environ, {}, clear=True), pytest.raises(SystemExit, match="1"):
            validate_all()


# ------------------------------------------------------------------ #
# Settings Validation                                                 #
# ------------------------------------------------------------------ #


class TestSettingsValidation:
    """Tests for Pydantic Settings validation of the secret key."""

    def test_settings_accepts_valid_key(self):
        """Test that Settings accepts a valid Fernet key."""
        key = Fernet.generate_key().decode()
        with patch.dict(os.environ, {"MISSIONCONTROL_SECRET_KEY": key}):
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.missioncontrol_secret_key == key

    def test_settings_rejects_empty_key(self):
        """Test that Settings rejects an empty key."""
        from pydantic import ValidationError

        with patch.dict(
            os.environ, {"MISSIONCONTROL_SECRET_KEY": ""}
        ):
            get_settings.cache_clear()
            with pytest.raises(ValidationError):
                get_settings()

    def test_settings_rejects_invalid_key(self):
        """Test that Settings rejects an invalid Fernet key."""
        from pydantic import ValidationError

        with patch.dict(
            os.environ, {"MISSIONCONTROL_SECRET_KEY": "not-valid"}
        ):
            get_settings.cache_clear()
            with pytest.raises(ValidationError):
                get_settings()

    def test_settings_key_validator_message(self):
        """Test that the validation error mentions Fernet key generation."""
        from pydantic import ValidationError

        with patch.dict(
            os.environ, {"MISSIONCONTROL_SECRET_KEY": "invalid"}
        ):
            get_settings.cache_clear()
            with pytest.raises(ValidationError) as exc_info:
                get_settings()
            error_msg = str(exc_info.value)
            assert "Fernet key" in error_msg

    def test_settings_reads_from_environment(self):
        """Test that Settings reads MISSIONCONTROL_SECRET_KEY from env."""
        key = Fernet.generate_key().decode()
        with patch.dict(os.environ, {"MISSIONCONTROL_SECRET_KEY": key}):
            get_settings.cache_clear()
            settings = get_settings()
        assert settings.missioncontrol_secret_key == key

    def test_settings_other_defaults_work(self):
        """Test that other settings have correct defaults alongside key."""
        key = Fernet.generate_key().decode()
        with patch.dict(os.environ, {"MISSIONCONTROL_SECRET_KEY": key}):
            get_settings.cache_clear()
            settings = get_settings()
        assert settings.project_name == "Mission Control"
        assert settings.environment == "development"
        assert settings.postgres_port == 5432

    def test_settings_cors_origins_parsed(self):
        """Test that CORS origins are parsed from comma-separated string."""
        key = Fernet.generate_key().decode()
        with patch.dict(os.environ, {"MISSIONCONTROL_SECRET_KEY": key}):
            get_settings.cache_clear()
            settings = get_settings()
        assert isinstance(settings.cors_origins, list)
        assert len(settings.cors_origins) >= 1


# ------------------------------------------------------------------ #
# Docker Environment Loading                                          #
# ------------------------------------------------------------------ #


class TestDockerEnvironmentLoading:
    """Tests simulating Docker environment variable loading."""

    def test_docker_env_simulation(self):
        """Test settings loading with a full Docker-like env."""
        key = Fernet.generate_key().decode()
        docker_env = {
            "MISSIONCONTROL_SECRET_KEY": key,
            "POSTGRES_DB": "mission_control",
            "POSTGRES_USER": "mission_control",
            "POSTGRES_PASSWORD": "secret",
            "POSTGRES_HOST": "postgres",
            "POSTGRES_PORT": "5432",
            "REDIS_HOST": "redis",
            "REDIS_PORT": "6379",
            "ENVIRONMENT": "production",
            "PROJECT_NAME": "Mission Control",
        }
        with patch.dict(os.environ, docker_env, clear=True):
            get_settings.cache_clear()
            settings = get_settings()
        assert settings.postgres_password == "secret"
        assert settings.environment == "production"
        assert "postgresql+psycopg://" in settings.database_url

    def test_database_url_computed_correctly(self):
        """Test that database_url is computed from individual parts."""
        key = Fernet.generate_key().decode()
        with patch.dict(os.environ, {"MISSIONCONTROL_SECRET_KEY": key}):
            get_settings.cache_clear()
            settings = get_settings()
        url = settings.database_url
        assert settings.postgres_user in url
        assert settings.postgres_host in url
        assert str(settings.postgres_port) in url
        assert settings.postgres_db in url

    def test_redis_url_computed_correctly(self):
        """Test that redis_url is computed correctly."""
        key = Fernet.generate_key().decode()
        with patch.dict(os.environ, {"MISSIONCONTROL_SECRET_KEY": key}):
            get_settings.cache_clear()
            settings = get_settings()
        assert settings.redis_url == "redis://redis:6379/0"

    def test_custom_remote_operation_settings(self):
        """Test custom remote operation settings in Docker env."""
        key = Fernet.generate_key().decode()
        with patch.dict(
            os.environ,
            {
                "MISSIONCONTROL_SECRET_KEY": key,
                "SSH_CONNECT_TIMEOUT": "15",
                "SSH_COMMAND_TIMEOUT": "120",
                "WINRM_CONNECT_TIMEOUT": "20",
                "REMOTE_RETRY_COUNT": "3",
            },
        ):
            get_settings.cache_clear()
            settings = get_settings()
        assert settings.ssh_connect_timeout == 15
        assert settings.ssh_command_timeout == 120
        assert settings.winrm_connect_timeout == 20
        assert settings.remote_retry_count == 3
