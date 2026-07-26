import os
import json
import urllib.request
import urllib.error

from validators import BaseValidator, CheckResult, Status, ValidatorResult


def _get(url, headers=None, timeout=5):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()) if e.read() else {}
    except Exception:
        return 0, {}


REQUIRED_MANIFEST_FIELDS = {"id", "name", "version", "type"}


class PluginsValidator(BaseValidator):
    name = "plugins"

    def run(self, config: dict):
        api = config["api_url"]
        project_root = config["project_root"]
        backend_dir = config.get("backend_dir", os.path.join(project_root, "backend"))
        plugins_dir = os.path.join(backend_dir, "plugins")

        checks = []
        checks.append(self._check("plugin_directory", lambda: self._check_plugin_dir(plugins_dir), critical=True))
        checks.append(self._check("plugin_manifests", lambda: self._check_manifests(plugins_dir), critical=False))
        checks.append(self._check("plugin_sdk_versions", lambda: self._check_sdk_versions(plugins_dir), critical=False))
        checks.append(self._check("duplicate_plugin_ids", lambda: self._check_duplicate_ids(plugins_dir), critical=True))
        checks.append(self._check("plugin_api_endpoint", lambda: self._check_api_endpoint(api), critical=False))
        checks.append(self._check("plugin_health", lambda: self._check_plugin_health(plugins_dir), critical=False))
        return ValidatorResult(module=self.name, checks=checks)

    def _check_plugin_dir(self, plugins_dir):
        if not os.path.isdir(plugins_dir):
            raise RuntimeError(f"Plugin directory not found: {plugins_dir}")
        return f"Plugin directory exists: {plugins_dir}"

    def _load_manifests(self, plugins_dir):
        manifests = []
        if not os.path.isdir(plugins_dir):
            return manifests
        for entry in os.listdir(plugins_dir):
            manifest_path = os.path.join(plugins_dir, entry, "manifest.json")
            if os.path.isfile(manifest_path):
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)
                manifests.append((entry, manifest))
        return manifests

    def _check_manifests(self, plugins_dir):
        manifests = self._load_manifests(plugins_dir)
        if not manifests:
            return CheckResult(
                name="plugin_manifests",
                status=Status.SKIP,
                message="No plugin manifests found",
            )
        errors = []
        for dirname, manifest in manifests:
            missing = REQUIRED_MANIFEST_FIELDS - set(manifest.keys())
            if missing:
                errors.append(f"{dirname}: missing fields {missing}")
        if errors:
            raise RuntimeError(f"Invalid manifests: {'; '.join(errors)}")
        return f"All {len(manifests)} plugin manifests have required fields"

    def _check_sdk_versions(self, plugins_dir):
        manifests = self._load_manifests(plugins_dir)
        if not manifests:
            return CheckResult(
                name="plugin_sdk_versions",
                status=Status.SKIP,
                message="No plugin manifests found",
            )
        incompatible = []
        for dirname, manifest in manifests:
            sdk_version = manifest.get("sdk_version", "")
            if sdk_version and not sdk_version.startswith("3.0"):
                incompatible.append(f"{dirname}: sdk_version={sdk_version}")
        if incompatible:
            raise RuntimeError(f"Incompatible SDK versions: {'; '.join(incompatible)}")
        return f"All {len(manifests)} plugins use compatible SDK versions"

    def _check_duplicate_ids(self, plugins_dir):
        manifests = self._load_manifests(plugins_dir)
        if not manifests:
            return CheckResult(
                name="duplicate_plugin_ids",
                status=Status.SKIP,
                message="No plugin manifests found",
            )
        ids = [manifest.get("id", dirname) for dirname, manifest in manifests]
        seen = {}
        duplicates = []
        for plugin_id in ids:
            if plugin_id in seen:
                duplicates.append(plugin_id)
            seen[plugin_id] = True
        if duplicates:
            raise RuntimeError(f"Duplicate plugin IDs: {', '.join(set(duplicates))}")
        return f"No duplicate plugin IDs found ({len(ids)} unique)"

    def _check_api_endpoint(self, api):
        status, body = _get(f"{api}/plugins")
        if status == 500:
            raise RuntimeError("GET /plugins returned 500")
        if status != 401:
            raise RuntimeError(f"GET /plugins returned {status}, expected 401 without auth")
        return "GET /plugins correctly returns 401"

    def _check_plugin_health(self, plugins_dir):
        manifests = self._load_manifests(plugins_dir)
        if not manifests:
            return CheckResult(
                name="plugin_health",
                status=Status.SKIP,
                message="No plugins to check",
            )
        errors = []
        for dirname, manifest in manifests:
            if not manifest.get("id"):
                errors.append(f"{dirname}: missing id")
            if not manifest.get("name"):
                errors.append(f"{dirname}: missing name")
        if errors:
            raise RuntimeError(f"Invalid manifests: {'; '.join(errors)}")
        return f"All {len(manifests)} plugins have valid manifests"
