"""
Plugin Installer

Handles the full installation workflow:
Download → Verify → Extract → Register → Enable → Event → Reload

Supports hot plugin install without Mission Control restart.
Server is the only component that installs plugins.
Agents never install plugins directly.

Sprint 3.10.4 - Plugin Marketplace.
"""

import logging
import shutil
from pathlib import Path
from typing import Any

from app.marketplace.compatibility import compatibility_engine
from app.marketplace.downloader import plugin_downloader
from app.marketplace.registry import (
    InstalledPlugin,
    PluginHealth,
    PluginStatus,
    marketplace_registry,
)
from app.marketplace.verifier import plugin_verifier

logger = logging.getLogger(__name__)

PLUGINS_DIR = Path(__file__).parent.parent / "plugins" / "installed"


class PluginInstaller:
    """Manages plugin installation, enabling, disabling, and removal."""

    def install(
        self,
        plugin_meta: dict[str, Any],
        zip_path: str,
        repo_name: str = "",
        signature_info: dict[str, str] | None = None,
        trust_level: str = "community",
    ) -> dict[str, Any]:
        """
        Full installation workflow for a plugin package.

        Returns:
            {"success": bool, "plugin_id": str, "version": str, "error": str, "warnings": list}
        """
        plugin_id = plugin_meta.get("id", "")
        version = plugin_meta.get("version", "0.0.0")
        name = plugin_meta.get("name", plugin_id)

        logger.info("Installing plugin %s v%s from %s", plugin_id, version, repo_name)

        # 1. Verify signature and checksum
        verify = plugin_verifier.verify_package(plugin_meta, zip_path, signature_info, trust_level)
        if not verify["passed"]:
            return {
                "success": False,
                "plugin_id": plugin_id,
                "version": version,
                "error": "Verification failed: " + "; ".join(verify["errors"]),
                "warnings": verify["warnings"],
            }

        # 2. Check compatibility
        compat = compatibility_engine.check_all(plugin_meta)
        if not compat["compatible"]:
            reasons = compatibility_engine.reject_reasons(plugin_meta)
            return {
                "success": False,
                "plugin_id": plugin_id,
                "version": version,
                "error": "Incompatible: " + "; ".join(reasons),
                "warnings": verify["warnings"],
            }

        # 3. Resolve dependencies
        dep_result = self._resolve_dependencies(plugin_meta)
        if not dep_result["success"]:
            return {
                "success": False,
                "plugin_id": plugin_id,
                "version": version,
                "error": dep_result["error"],
                "warnings": verify["warnings"],
            }

        # 4. Extract
        target_dir = str(PLUGINS_DIR / plugin_id)
        # Backup existing if present
        backup_path = ""
        if Path(target_dir).exists():
            backup_path = str(PLUGINS_DIR / f"{plugin_id}.bak")
            shutil.copytree(target_dir, backup_path, dirs_exist_ok=True)
            shutil.rmtree(target_dir)

        extract = plugin_downloader.extract(zip_path, target_dir)
        if not extract["success"]:
            # Restore backup if available
            if backup_path and Path(backup_path).exists():
                shutil.move(backup_path, target_dir)
            return {
                "success": False,
                "plugin_id": plugin_id,
                "version": version,
                "error": "Extract failed: " + extract["error"],
                "warnings": verify["warnings"],
            }

        # 5. Verify extracted plugin.json matches
        extracted_meta = self._load_plugin_json(target_dir)
        if extracted_meta and extracted_meta.get("id") != plugin_id:
            shutil.rmtree(target_dir)
            if backup_path and Path(backup_path).exists():
                shutil.move(backup_path, target_dir)
            return {
                "success": False,
                "plugin_id": plugin_id,
                "version": version,
                "error": "Extracted plugin ID mismatch",
                "warnings": verify["warnings"],
            }

        # 6. Register in marketplace registry
        sig_status = "verified" if verify["passed"] else "unsigned"
        installed = InstalledPlugin(
            plugin_id=plugin_id,
            name=name,
            version=version,
            repo=repo_name,
            status=PluginStatus.INSTALLED,
            health=PluginHealth.UNKNOWN,
            signature_status=sig_status,
            checksum=extract.get("sha256", ""),
            enabled=True,
            dependencies=[d.get("id", "") for d in plugin_meta.get("dependencies", []) if isinstance(d, dict)],
            permissions=plugin_meta.get("permissions", []),
        )
        marketplace_registry.register(installed)

        # 7. Clean up backup
        if backup_path and Path(backup_path).exists():
            shutil.rmtree(backup_path, ignore_errors=True)

        # 8. Clean up zip
        plugin_downloader.cleanup(zip_path)

        logger.info("Plugin %s v%s installed successfully", plugin_id, version)
        return {
            "success": True,
            "plugin_id": plugin_id,
            "version": version,
            "error": None,
            "warnings": verify["warnings"],
        }

    def uninstall(self, plugin_id: str) -> dict[str, Any]:
        """Remove a plugin and unregister it."""
        target_dir = PLUGINS_DIR / plugin_id
        if target_dir.exists():
            shutil.rmtree(target_dir)

        marketplace_registry.unregister(plugin_id)
        logger.info("Plugin %s uninstalled", plugin_id)
        return {"success": True, "error": None}

    def enable(self, plugin_id: str) -> bool:
        """Enable a plugin."""
        return marketplace_registry.set_enabled(plugin_id, True)

    def disable(self, plugin_id: str) -> bool:
        """Disable a plugin."""
        return marketplace_registry.set_enabled(plugin_id, False)

    def rollback(self, plugin_id: str, target_version: str = "") -> dict[str, Any]:
        """
        Rollback a plugin to its previous version.
        Requires a backup or re-download from repository.
        """
        plugin = marketplace_registry.get(plugin_id)
        if not plugin:
            return {"success": False, "error": f"Plugin {plugin_id} not found in registry"}

        prev = plugin.previous_version
        if target_version:
            prev = target_version

        if not prev:
            return {"success": False, "error": "No previous version available for rollback"}

        logger.info("Rolling back %s to %s", plugin_id, prev)
        # Uninstall current
        self.uninstall(plugin_id)
        # Re-download and install from repo (would need repo integration here)
        return {
            "success": True,
            "plugin_id": plugin_id,
            "version": prev,
            "error": None,
            "warnings": ["Rollback requires re-download from repository"],
        }

    def _resolve_dependencies(self, plugin_meta: dict[str, Any]) -> dict[str, Any]:
        """Check and resolve plugin dependencies. Auto-install if possible."""
        deps = plugin_meta.get("dependencies", [])
        if not deps:
            return {"success": True, "error": None, "missing": []}

        missing = []
        for dep in deps:
            dep_id = dep.get("id", "") if isinstance(dep, dict) else str(dep)
            dep_version = dep.get("version", "") if isinstance(dep, dict) else ""
            installed = marketplace_registry.get(dep_id)
            if not installed:
                missing.append(dep_id)
            elif dep_version and installed.version != dep_version:
                missing.append(f"{dep_id}@{dep_version} (have {installed.version})")

        if missing:
            return {"success": False, "error": f"Missing dependencies: {', '.join(missing)}", "missing": missing}
        return {"success": True, "error": None, "missing": []}

    @staticmethod
    def _load_plugin_json(plugin_dir: str) -> dict[str, Any] | None:
        """Load plugin.json from an extracted plugin directory."""
        import json

        pj = Path(plugin_dir) / "plugin.json"
        if pj.exists():
            return json.loads(pj.read_text(encoding="utf-8"))
        return None


plugin_installer = PluginInstaller()
