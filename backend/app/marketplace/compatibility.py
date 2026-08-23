"""
Compatibility Engine

Validates plugin compatibility across multiple dimensions:
- SDK version
- Python version
- Edition (community/enterprise)
- Platform (linux/windows/macos)
- Dependencies
- Database version
- Agent version

Sprint 3.10.4 - Plugin Marketplace.
"""

import logging
import sys
from typing import Any

logger = logging.getLogger(__name__)


class CompatibilityEngine:
    """Validates plugin compatibility across all dimensions."""

    # Current system versions
    CURRENT_SDK = "3.10"
    CURRENT_PYTHON = f"{sys.version_info.major}.{sys.version_info.minor}"
    CURRENT_EDITION = "community"
    CURRENT_PLATFORM = {"linux": "linux", "win32": "windows", "darwin": "macos"}.get(sys.platform, sys.platform)
    CURRENT_DATABASE = "16"
    CURRENT_AGENT = "3.10"

    def check_all(self, plugin_meta: dict[str, Any]) -> dict[str, Any]:
        """Run all compatibility checks."""
        results = {
            "sdk": self.check_sdk(plugin_meta),
            "python": self.check_python(plugin_meta),
            "edition": self.check_edition(plugin_meta),
            "platform": self.check_platform(plugin_meta),
            "database": self.check_database(plugin_meta),
            "agent": self.check_agent(plugin_meta),
            "dependencies": self.check_dependencies(plugin_meta),
        }
        compatible = all(r["compatible"] for r in results.values())
        return {"compatible": compatible, "checks": results}

    def check_sdk(self, meta: dict[str, Any]) -> dict[str, Any]:
        required = meta.get("sdk_version", "")
        if not required:
            return {"compatible": True, "required": "", "current": self.CURRENT_SDK, "message": "No SDK constraint"}
        try:
            req = [int(x) for x in required.split(".")[:2]]
            cur = [int(x) for x in self.CURRENT_SDK.split(".")[:2]]
            if req[0] != cur[0]:
                return {"compatible": False, "required": required, "current": self.CURRENT_SDK, "message": f"Major mismatch: need {required}, have {self.CURRENT_SDK}"}
            if req[1] > cur[1]:
                return {"compatible": False, "required": required, "current": self.CURRENT_SDK, "message": f"Too new: need <= {required}, have {self.CURRENT_SDK}"}
            return {"compatible": True, "required": required, "current": self.CURRENT_SDK, "message": "Compatible"}
        except (ValueError, IndexError):
            return {"compatible": True, "required": required, "current": self.CURRENT_SDK, "message": "Unparseable, assuming compatible"}

    def check_python(self, meta: dict[str, Any]) -> dict[str, Any]:
        required = meta.get("python_version", "")
        if not required:
            return {"compatible": True, "required": "", "current": self.CURRENT_PYTHON, "message": "No Python constraint"}
        if self.CURRENT_PYTHON in required or "*" in required:
            return {"compatible": True, "required": required, "current": self.CURRENT_PYTHON, "message": "Compatible"}
        return {"compatible": False, "required": required, "current": self.CURRENT_PYTHON, "message": f"Need Python {required}, have {self.CURRENT_PYTHON}"}

    def check_edition(self, meta: dict[str, Any]) -> dict[str, Any]:
        supported = meta.get("editions", ["community", "enterprise"])
        if self.CURRENT_EDITION in supported or "all" in supported:
            return {"compatible": True, "supported": supported, "current": self.CURRENT_EDITION, "message": "Compatible"}
        return {"compatible": False, "supported": supported, "current": self.CURRENT_EDITION, "message": f"Needs {supported}, have {self.CURRENT_EDITION}"}

    def check_platform(self, meta: dict[str, Any]) -> dict[str, Any]:
        supported = meta.get("platforms", ["linux", "windows", "macos"])
        if self.CURRENT_PLATFORM in supported or "all" in supported:
            return {"compatible": True, "supported": supported, "current": self.CURRENT_PLATFORM, "message": "Compatible"}
        return {"compatible": False, "supported": supported, "current": self.CURRENT_PLATFORM, "message": f"Needs {supported}, have {self.CURRENT_PLATFORM}"}

    def check_database(self, meta: dict[str, Any]) -> dict[str, Any]:
        required = meta.get("database_version", "")
        if not required:
            return {"compatible": True, "required": "", "current": self.CURRENT_DATABASE, "message": "No DB constraint"}
        if self.CURRENT_DATABASE in required:
            return {"compatible": True, "required": required, "current": self.CURRENT_DATABASE, "message": "Compatible"}
        return {"compatible": False, "required": required, "current": self.CURRENT_DATABASE, "message": f"Need DB {required}, have {self.CURRENT_DATABASE}"}

    def check_agent(self, meta: dict[str, Any]) -> dict[str, Any]:
        required = meta.get("agent_version", "")
        if not required:
            return {"compatible": True, "required": "", "current": self.CURRENT_AGENT, "message": "No agent constraint"}
        if self.CURRENT_AGENT in required or "*" in required:
            return {"compatible": True, "required": required, "current": self.CURRENT_AGENT, "message": "Compatible"}
        return {"compatible": False, "required": required, "current": self.CURRENT_AGENT, "message": f"Need agent {required}, have {self.CURRENT_AGENT}"}

    def check_dependencies(self, meta: dict[str, Any]) -> dict[str, Any]:
        deps = meta.get("dependencies", [])
        if not deps:
            return {"compatible": True, "missing": [], "message": "No dependencies"}
        # Placeholder: real implementation queries installed plugins
        return {"compatible": True, "missing": [], "message": f"{len(deps)} dependencies declared (verified at install time)"}

    def reject_reasons(self, plugin_meta: dict[str, Any]) -> list[str]:
        """Return a list of rejection reasons, empty if compatible."""
        results = self.check_all(plugin_meta)
        reasons = []
        for name, check in results["checks"].items():
            if not check["compatible"]:
                reasons.append(f"{name}: {check['message']}")
        return reasons


compatibility_engine = CompatibilityEngine()
