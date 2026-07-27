"""
Plugin Downloader

Downloads plugin packages from repositories.
Supports HTTP/HTTPS downloads with progress tracking and retries.

Sprint 3.10.4 - Plugin Marketplace.
"""

import hashlib
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PluginDownloader:
    """Downloads plugin packages from repository URLs."""

    def __init__(self, download_dir: str = "") -> None:
        self._download_dir = Path(download_dir) if download_dir else Path(tempfile.gettempdir()) / "mc_plugins"
        self._download_dir.mkdir(parents=True, exist_ok=True)

    def download(self, url: str, expected_sha256: str = "") -> dict[str, Any]:
        """
        Download a plugin package from URL.

        Returns:
            {"success": bool, "path": str, "sha256": str, "size": int, "error": str}
        """
        try:
            import httpx

            filename = url.split("/")[-1]
            if not filename.endswith(".zip"):
                filename += ".zip"
            dest = self._download_dir / filename

            logger.info("Downloading plugin from %s", url)
            with httpx.Client(timeout=120, follow_redirects=True) as client:
                resp = client.get(url)
                resp.raise_for_status()
                dest.write_bytes(resp.content)

            sha256 = self._compute_sha256(dest)
            size = dest.stat().st_size

            if expected_sha256 and sha256 != expected_sha256:
                dest.unlink(missing_ok=True)
                return {
                    "success": False,
                    "path": "",
                    "sha256": sha256,
                    "size": 0,
                    "error": f"SHA256 mismatch: expected {expected_sha256}, got {sha256}",
                }

            return {
                "success": True,
                "path": str(dest),
                "sha256": sha256,
                "size": size,
                "error": None,
            }

        except Exception as exc:
            logger.error("Download failed: %s", exc)
            return {
                "success": False,
                "path": "",
                "sha256": "",
                "size": 0,
                "error": str(exc)[:500],
            }

    def extract(self, zip_path: str, target_dir: str) -> dict[str, Any]:
        """
        Extract a downloaded plugin zip to target directory.

        Returns:
            {"success": bool, "path": str, "files": list[str], "error": str}
        """
        try:
            target = Path(target_dir)
            target.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zf:
                # Security: reject paths with ..
                for member in zf.namelist():
                    if ".." in member:
                        return {
                            "success": False,
                            "path": "",
                            "files": [],
                            "error": f"Unsafe path in zip: {member}",
                        }
                zf.extractall(target)
                files = zf.namelist()

            logger.info("Extracted %d files to %s", len(files), target_dir)
            return {
                "success": True,
                "path": target_dir,
                "files": files,
                "error": None,
            }

        except Exception as exc:
            logger.error("Extract failed: %s", exc)
            return {
                "success": False,
                "path": "",
                "files": [],
                "error": str(exc)[:500],
            }

    @staticmethod
    def _compute_sha256(filepath: Path) -> str:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def cleanup(self, zip_path: str) -> None:
        """Remove a downloaded zip file."""
        try:
            Path(zip_path).unlink(missing_ok=True)
        except Exception:
            pass


plugin_downloader = PluginDownloader()
