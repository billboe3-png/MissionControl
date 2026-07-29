"""
Plugin Signature Verification

Verifies plugin package integrity using SHA256, Ed25519, and RSA signatures.
Official Mission Control signatures are verified against known public keys.
Unsigned plugins are allowed with warnings for community trust level.

Sprint 3.10.4 - Plugin Marketplace.
"""

import hashlib
import logging
from enum import StrEnum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SignatureAlgorithm(StrEnum):
    SHA256 = "sha256"
    ED25519 = "ed25519"
    RSA = "rsa"
    NONE = "none"


class SignatureStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    UNSIGNED = "unsigned"
    VERIFIED = "verified"
    FAILED = "failed"


class PluginSigner:
    """Verifies plugin package signatures."""

    def __init__(self) -> None:
        self._official_keys: dict[str, str] = {}

    def register_official_key(self, plugin_id: str, public_key: str) -> None:
        """Register an official public key for a plugin."""
        self._official_keys[plugin_id] = public_key

    def verify_checksum(self, file_path: str, expected_sha256: str) -> dict[str, Any]:
        """Verify SHA256 checksum of a file."""
        try:
            h = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            actual = h.hexdigest()

            valid = actual == expected_sha256
            return {
                "status": SignatureStatus.VERIFIED if valid else SignatureStatus.INVALID,
                "algorithm": SignatureAlgorithm.SHA256,
                "expected": expected_sha256,
                "actual": actual,
                "valid": valid,
                "error": None if valid else "Checksum mismatch",
            }
        except Exception as exc:
            return {
                "status": SignatureStatus.FAILED,
                "algorithm": SignatureAlgorithm.SHA256,
                "expected": expected_sha256,
                "actual": "",
                "valid": False,
                "error": str(exc)[:500],
            }

    def verify_ed25519(self, file_path: str, signature_b64: str, public_key_b64: str) -> dict[str, Any]:
        """Verify Ed25519 signature of a file."""
        try:
            import base64

            from cryptography.hazmat.primitives.asymmetric.ed25519 import (
                Ed25519PublicKey,
            )
            from cryptography.hazmat.primitives.serialization import load_der_public_key

            data = Path(file_path).read_bytes()
            sig = base64.b64decode(signature_b64)
            pub_bytes = base64.b64decode(public_key_b64)

            key = load_der_public_key(pub_bytes)
            if not isinstance(key, Ed25519PublicKey):
                return {
                    "status": SignatureStatus.INVALID,
                    "algorithm": SignatureAlgorithm.ED25519,
                    "valid": False,
                    "error": "Not an Ed25519 public key",
                }

            key.verify(sig, data)
            return {
                "status": SignatureStatus.VERIFIED,
                "algorithm": SignatureAlgorithm.ED25519,
                "valid": True,
                "error": None,
            }

        except Exception as exc:
            return {
                "status": SignatureStatus.FAILED,
                "algorithm": SignatureAlgorithm.ED25519,
                "valid": False,
                "error": str(exc)[:500],
            }

    def verify_rsa(self, file_path: str, signature_b64: str, public_key_pem: str) -> dict[str, Any]:
        """Verify RSA signature of a file."""
        try:
            import base64

            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding

            data = Path(file_path).read_bytes()
            sig = base64.b64decode(signature_b64)

            key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
            key.verify(sig, data, padding.PKCS1v15(), hashes.SHA256())

            return {
                "status": SignatureStatus.VERIFIED,
                "algorithm": SignatureAlgorithm.RSA,
                "valid": True,
                "error": None,
            }

        except Exception as exc:
            return {
                "status": SignatureStatus.FAILED,
                "algorithm": SignatureAlgorithm.RSA,
                "valid": False,
                "error": str(exc)[:500],
            }

    def verify_plugin(
        self,
        file_path: str,
        signature_info: dict[str, str] | None,
        plugin_id: str = "",
    ) -> dict[str, Any]:
        """
        Verify a plugin package using the best available method.

        Args:
            file_path: Path to the plugin zip
            signature_info: {"algorithm": str, "signature": str, "public_key": str, "sha256": str}
            plugin_id: Plugin ID for official key lookup

        Returns:
            {"valid": bool, "algorithm": str, "status": str, "details": list}
        """
        details: list[dict[str, Any]] = []

        # Always verify checksum if provided
        if signature_info and "sha256" in signature_info:
            cs = self.verify_checksum(file_path, signature_info["sha256"])
            details.append(cs)
            if not cs["valid"]:
                return {"valid": False, "algorithm": "sha256", "status": "invalid", "details": details}

        # Verify signature if provided
        algo = (signature_info or {}).get("algorithm", "")
        sig = (signature_info or {}).get("signature", "")
        key = (signature_info or {}).get("public_key", "")

        if algo == "ed25519" and sig and key:
            r = self.verify_ed25519(file_path, sig, key)
            details.append(r)
            if not r["valid"]:
                return {"valid": False, "algorithm": algo, "status": "invalid", "details": details}

        elif algo == "rsa" and sig and key:
            r = self.verify_rsa(file_path, sig, key)
            details.append(r)
            if not r["valid"]:
                return {"valid": False, "algorithm": algo, "status": "invalid", "details": details}

        elif plugin_id and plugin_id in self._official_keys:
            # Try official key if no signature provided but we have an official key
            official_key = self._official_keys[plugin_id]
            if algo == "ed25519" and sig:
                r = self.verify_ed25519(file_path, sig, official_key)
                details.append(r)
                if not r["valid"]:
                    return {"valid": False, "algorithm": algo, "status": "invalid", "details": details}

        elif not sig:
            details.append({
                "status": SignatureStatus.UNSIGNED,
                "algorithm": SignatureAlgorithm.NONE,
                "valid": False,
                "error": "No signature provided",
            })

        return {"valid": True, "algorithm": algo or "sha256", "status": "verified", "details": details}


plugin_signer = PluginSigner()
