"""
Mission Control Security Module

Sprint 2.1.4 - Secure Credential Vault.

Provides encryption/decryption for sensitive credential data at rest
using Fernet symmetric encryption (AES-128-CBC with HMAC-SHA256).
"""

import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class CredentialCipher:
    """
    Fernet-based encrypt/decrypt for credential fields.

    Usage:
        cipher = CredentialCipher(settings.missioncontrol_secret_key)
        encrypted = cipher.encrypt("my-secret-password")
        decrypted = cipher.decrypt(encrypted)
    """

    def __init__(self, secret_key: str) -> None:
        """
        Initialize the cipher with a Fernet secret key.

        Args:
            secret_key: A valid Fernet key (URL-safe base64-encoded 32 bytes).

        Raises:
            ValueError: If the key is invalid.
        """
        if not secret_key:
            raise ValueError("Secret key must not be empty")

        try:
            key_bytes = (
                secret_key.encode()
                if isinstance(secret_key, str)
                else secret_key
            )
            self._fernet = Fernet(key_bytes)
        except Exception as exc:
            raise ValueError(
                "Invalid Fernet key. Generate one with: "
                "python -c \"from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())\""
            ) from exc

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt.

        Returns:
            The encrypted string (URL-safe base64-encoded).

        Raises:
            ValueError: If encryption fails.
        """
        if not plaintext:
            return plaintext

        try:
            token = self._fernet.encrypt(plaintext.encode("utf-8"))
            return token.decode("utf-8")
        except Exception as exc:
            logger.error("Encryption failed: %s", type(exc).__name__)
            raise ValueError("Encryption failed") from exc

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a ciphertext string.

        Args:
            ciphertext: The encrypted string to decrypt.

        Returns:
            The decrypted plaintext string.

        Raises:
            ValueError: If decryption fails (wrong key, corrupted data).
        """
        if not ciphertext:
            return ciphertext

        try:
            plaintext = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return plaintext.decode("utf-8")
        except InvalidToken as exc:
            logger.error("Decryption failed: invalid token or wrong key")
            raise ValueError(
                "Decryption failed: invalid ciphertext or wrong key"
            ) from exc
        except Exception as exc:
            logger.error("Decryption failed: %s", type(exc).__name__)
            raise ValueError("Decryption failed") from exc


def get_credential_cipher() -> CredentialCipher:
    """
    Get a CredentialCipher instance using the application settings.

    Returns:
        A configured CredentialCipher instance.

    Raises:
        ValueError: If MISSIONCONTROL_SECRET_KEY is not configured.
    """
    from app.core.config import get_settings

    settings = get_settings()
    return CredentialCipher(settings.missioncontrol_secret_key)
