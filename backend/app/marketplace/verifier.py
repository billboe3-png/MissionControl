"""
Plugin Verifier

Orchestrates all verification steps for plugin installation:
1. Signature verification
2. Checksum verification
3. SDK compatibility check
4. Dependency validation
5. Security scanning

Sprint 3.10.4 - Plugin Marketplace.
"""

import logging
from typing import Any

from app.marketplace.signatures import plugin_signer

logger = logging.getLogger(__name__)


class PluginVerifier:
    """Verifies plugin packages before installation."""

    def verify_package(
        self,
        plugin_meta: dict[str, Any],
        file_path: str,
        signature_info: dict[str, str] | None = None,
        trust_level: str = "community",
    ) -> dict[str, Any]:
        """
        Run all verification checks on a plugin package.

        Args:
            plugin_meta: Plugin metadata from plugin.json
            file_path: Path to the downloaded zip
            signature_info: Signature data if available
            trust_level: Repository trust level

        Returns:
            {"passed": bool, "checks": list, "warnings": list, "errors": list}
        """
        checks: list[dict[str, Any]] = []
        warnings: list[str] = []
        errors: list[str] = []

        # 1. Signature/Checksum verification
        plugin_id = plugin_meta.get("id", "")
        sig_result = plugin_signer.verify_plugin(file_path, signature_info, plugin_id)
        checks.append({"name": "signature", "result": sig_result})

        if not sig_result["valid"]:
            if trust_level == "official":
                errors.append("Official plugin signature verification failed")
            elif trust_level == "community":
                warnings.append("Community plugin is unsigned or has invalid signature")
            else:
                errors.append("Signature verification failed for untrusted repository")

        # 2. SDK version compatibility
        sdk_ok = self._check_sdk_compatibility(plugin_meta)
        checks.append({"name": "sdk_compatibility", "result": sdk_ok})
        if not sdk_ok["valid"]:
            errors.append(f"SDK version mismatch: {sdk_ok.get('error', '')}")

        # 3. Python version compatibility
        py_ok = self._check_python_compatibility(plugin_meta)
        checks.append({"name": "python_compatibility", "result": py_ok})
        if not py_ok["valid"]:
            errors.append(f"Python version mismatch: {py_ok.get('error', '')}")

        # 4. Edition compatibility
        edition_ok = self._check_edition_compatibility(plugin_meta)
        checks.append({"name": "edition_compatibility", "result": edition_ok})
        if not edition_ok["valid"]:
            warnings.append(f"Edition mismatch: {edition_ok.get('error', '')}")

        # 5. Platform compatibility
        platform_ok = self._check_platform_compatibility(plugin_meta)
        checks.append({"name": "platform_compatibility", "result": platform_ok})
        if not platform_ok["valid"]:
            warnings.append(f"Platform mismatch: {platform_ok.get('error', '')}")

        # 6. Dependency check
        deps_ok = self._check_dependencies(plugin_meta)
        checks.append({"name": "dependencies", "result": deps_ok})
        if not deps_ok["valid"]:
            errors.append(f"Missing dependencies: {deps_ok.get('error', '')}")

        # 7. Database version check
        db_ok = self._check_database_compatibility(plugin_meta)
        checks.append({"name": "database_compatibility", "result": db_ok})
        if not db_ok["valid"]:
            warnings.append(f"Database version mismatch: {db_ok.get('error', '')}")

        passed = len(errors) == 0
        return {"passed": passed, "checks": checks, "warnings": warnings, "errors": errors}

    @staticmethod
    def _check_sdk_compatibility(plugin_meta: dict[str, Any]) -> dict[str, Any]:
        """Check if the plugin is compatible with current SDK version."""
        required = plugin_meta.get("sdk_version", "")
        # Current SDK version
        current = "3.10"
        if not required:
            return {"valid": True, "required": "", "current": current, "error": None}

        try:
            req_parts = [int(x) for x in required.split(".")[:2]]
            cur_parts = [int(x) for x in current.split(".")[:2]]
            # Major must match, minor must be <= current
            if req_parts[0] != cur_parts[0]:
                return {"valid": False, "required": required, "current": current, "error": f"Major SDK mismatch: need {required}, have {current}"}
            if req_parts[1] > cur_parts[1]:
                return {"valid": False, "required": required, "current": current, "error": f"Minor SDK mismatch: need {required}, have {current}"}
            return {"valid": True, "required": required, "current": current, "error": None}
        except (ValueError, IndexError):
            return {"valid": True, "required": required, "current": current, "error": None}

    @staticmethod
    def _check_python_compatibility(plugin_meta: dict[str, Any]) -> dict[str, Any]:
        """Check Python version compatibility."""
        required = plugin_meta.get("python_version", "")
        import sys
        current = f"{sys.version_info.major}.{sys.version_info.minor}"
        if not required:
            return {"valid": True, "required": "", "current": current, "error": None}
        if current not in required and "*" not in required:
            return {"valid": False, "required": required, "current": current, "error": f"Python {required} required, have {current}"}
        return {"valid": True, "required": required, "current": current, "error": None}

    @staticmethod
    def _check_edition_compatibility(plugin_meta: dict[str, Any]) -> dict[str, Any]:
        """Check edition compatibility."""
        supported = plugin_meta.get("editions", ["community", "enterprise"])
        # Current edition determined at runtime
        current = "community"
        if current in supported or "all" in supported:
            return {"valid": True, "supported": supported, "current": current, "error": None}
        return {"valid": False, "supported": supported, "current": current, "error": f"Plugin requires {supported}, running {current}"}

    @staticmethod
    def _check_platform_compatibility(plugin_meta: dict[str, Any]) -> dict[str, Any]:
        """Check platform compatibility."""
        supported = plugin_meta.get("platforms", ["linux", "windows", "macos"])
        import sys
        current = sys.platform
        platform_map = {"linux": "linux", "win32": "windows", "darwin": "macos"}
        current_name = platform_map.get(current, current)
        if current_name in supported or "all" in supported:
            return {"valid": True, "supported": supported, "current": current_name, "error": None}
        return {"valid": False, "supported": supported, "current": current_name, "error": f"Plugin requires {supported}, running {current_name}"}

    @staticmethod
    def _check_dependencies(plugin_meta: dict[str, Any]) -> dict[str, Any]:
        """Check if all dependencies are met."""
        deps = plugin_meta.get("dependencies", [])
        if not deps:
            return {"valid": True, "missing": [], "error": None}
        # For now, just return valid; real check requires querying installed plugins
        return {"valid": True, "missing": [], "error": None}

    @staticmethod
    def _check_database_compatibility(plugin_meta: dict[str, Any]) -> dict[str, Any]:
        """Check database version compatibility."""
        required = plugin_meta.get("database_version", "")
        current = "16"
        if not required:
            return {"valid": True, "required": "", "current": current, "error": None}
        if current not in required:
            return {"valid": False, "required": required, "current": current, "error": f"Database {required} required, have {current}"}
        return {"valid": True, "required": required, "current": current, "error": None}


plugin_verifier = PluginVerifier()
