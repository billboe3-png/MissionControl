"""
Credential Cipher Security Tests

Sprint 2.1.4 - Secure Credential Vault.
"""

import pytest
from cryptography.fernet import Fernet

from app.core.security import CredentialCipher


class TestCredentialCipher:
    """Tests for the CredentialCipher encryption/decryption."""

    def test_encrypt_decrypt_round_trip(self):
        """Test that encrypt/decrypt produces the original value."""
        key = Fernet.generate_key().decode()
        cipher = CredentialCipher(key)

        plaintext = "my-secret-password-123!"
        encrypted = cipher.encrypt(plaintext)
        decrypted = cipher.decrypt(encrypted)

        assert decrypted == plaintext
        assert encrypted != plaintext

    def test_encrypt_empty_string(self):
        """Test that encrypting an empty string returns empty."""
        key = Fernet.generate_key().decode()
        cipher = CredentialCipher(key)

        assert cipher.encrypt("") == ""

    def test_decrypt_empty_string(self):
        """Test that decrypting an empty string returns empty."""
        key = Fernet.generate_key().decode()
        cipher = CredentialCipher(key)

        assert cipher.decrypt("") == ""

    def test_encrypt_none_like_empty(self):
        """Test that encrypting None-like value returns it."""
        key = Fernet.generate_key().decode()
        cipher = CredentialCipher(key)

        # Should not raise
        assert cipher.encrypt("") == ""

    def test_invalid_key_too_short(self):
        """Test that an invalid key raises ValueError."""
        with pytest.raises(ValueError, match="Invalid Fernet key"):
            CredentialCipher("to-short-key")

    def test_invalid_key_wrong_format(self):
        """Test that a non-base64 key raises ValueError."""
        with pytest.raises(ValueError, match="Invalid Fernet key"):
            CredentialCipher("not-a-valid-fernet-key-at-all!")

    def test_empty_key(self):
        """Test that an empty key raises ValueError."""
        with pytest.raises(ValueError, match="Secret key must not be empty"):
            CredentialCipher("")

    def test_wrong_key_cannot_decrypt(self):
        """Test that a different key cannot decrypt data."""
        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()

        cipher1 = CredentialCipher(key1)
        cipher2 = CredentialCipher(key2)

        encrypted = cipher1.encrypt("secret-data")

        with pytest.raises(ValueError, match="Decryption failed"):
            cipher2.decrypt(encrypted)

    def test_corrupted_ciphertext(self):
        """Test that corrupted ciphertext raises ValueError."""
        key = Fernet.generate_key().decode()
        cipher = CredentialCipher(key)

        encrypted = cipher.encrypt("valid-data")
        corrupted = encrypted[:-5] + "XXXXX"

        with pytest.raises(ValueError, match="Decryption failed"):
            cipher.decrypt(corrupted)

    def test_deterministic_encryption(self):
        """Test that encryption produces different ciphertext each time (random IV)."""
        key = Fernet.generate_key().decode()
        cipher = CredentialCipher(key)

        plaintext = "same-password"
        enc1 = cipher.encrypt(plaintext)
        enc2 = cipher.encrypt(plaintext)

        # Fernet uses random IV, so ciphertext should differ
        assert enc1 != enc2
        # But both should decrypt to the same value
        assert cipher.decrypt(enc1) == plaintext
        assert cipher.decrypt(enc2) == plaintext

    def test_special_characters(self):
        """Test encryption of special characters and unicode."""
        key = Fernet.generate_key().decode()
        cipher = CredentialCipher(key)

        plaintext = "p@$$w0rd!#%&*()_+{}|:<>?café"
        encrypted = cipher.encrypt(plaintext)
        decrypted = cipher.decrypt(encrypted)

        assert decrypted == plaintext

    def test_long_password(self):
        """Test encryption of a very long password."""
        key = Fernet.generate_key().decode()
        cipher = CredentialCipher(key)

        plaintext = "x" * 10000
        encrypted = cipher.encrypt(plaintext)
        decrypted = cipher.decrypt(encrypted)

        assert decrypted == plaintext

    def test_ssh_key_format(self):
        """Test encryption of SSH private key format."""
        key = Fernet.generate_key().decode()
        cipher = CredentialCipher(key)

        ssh_key = (
            "-----BEGIN OPENSSH PRIVATE KEY-----\n"
            "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAE\n"
            "-----END OPENSSH PRIVATE KEY-----"
        )
        encrypted = cipher.encrypt(ssh_key)
        decrypted = cipher.decrypt(encrypted)

        assert decrypted == ssh_key

    def test_bytes_key(self):
        """Test that bytes key also works."""
        key = Fernet.generate_key()
        cipher = CredentialCipher(key)

        plaintext = "bytes-key-test"
        encrypted = cipher.encrypt(plaintext)
        decrypted = cipher.decrypt(encrypted)

        assert decrypted == plaintext


class TestGetCredentialCipher:
    """Tests for the get_credential_cipher factory."""

    def test_get_cipher_with_settings(self, monkeypatch):
        """Test getting cipher from settings."""
        from app.core.security import get_credential_cipher

        test_key = Fernet.generate_key().decode()
        monkeypatch.setenv("MISSIONCONTROL_SECRET_KEY", test_key)

        # Clear lru_cache
        from app.core.config import get_settings
        get_settings.cache_clear()

        cipher = get_credential_cipher()
        assert cipher is not None
        assert isinstance(cipher, CredentialCipher)
