"""
MikroTik Connector Unit Tests

SSH / Telnet / REST connectors tested against mocked transports
(netmiko ConnectHandler and requests.Session).
"""

import json
from typing import ClassVar

import pytest

from app.plugins.installed.official_mikrotik.connector.base import ConnectorConfig
from app.plugins.installed.official_mikrotik.connector.exceptions import (
    CommandError,
    ConnectorAuthenticationError,
    ConnectorCommandError,
    ConnectorConnectionError,
)
from app.plugins.installed.official_mikrotik.connector.exceptions import (
    ConnectionError as LegacyConnectionError,
)
from app.plugins.installed.official_mikrotik.connector.ssh import SshConnector
from app.plugins.installed.official_mikrotik.connector.telnet import TelnetConnector
from app.plugins.installed.official_mikrotik.connector.webui import (
    RestConnector,
    WebUiConnector,
)

PASSWORD = "unit-test-secret"


def _config(**overrides):
    defaults = {
        "host": "10.0.0.1",
        "username": "admin",
        "password": PASSWORD,
    }
    defaults.update(overrides)
    return ConnectorConfig(**defaults)


class FakeNetmikoHandler:
    """Captured-constructor fake standing in for netmiko.ConnectHandler."""

    instances: ClassVar[list["FakeNetmikoHandler"]] = []

    def __init__(self, **kwargs):
        self.params = kwargs
        self.commands: list[str] = []
        self.outputs: dict[str, str] = {}
        self.disconnected = False
        FakeNetmikoHandler.instances.append(self)

    def send_command(self, command, strip_command=False, strip_prompt=False):
        assert strip_command is False
        assert strip_prompt is False
        self.commands.append(command)
        return self.outputs.get(command, f"echo:{command}")

    def disconnect(self):
        self.disconnected = True


@pytest.fixture(autouse=True)
def _reset_fake_handler():
    FakeNetmikoHandler.instances = []
    yield
    FakeNetmikoHandler.instances = []


# ---------------------------------------------------------------------- #
# Exceptions / aliases                                                    #
# ---------------------------------------------------------------------- #


class TestConnectorExceptions:
    def test_backwards_compatible_aliases(self):
        assert LegacyConnectionError is ConnectorConnectionError
        assert CommandError is ConnectorCommandError

    def test_auth_error_is_connection_error(self):
        assert issubclass(ConnectorAuthenticationError, ConnectorConnectionError)


# ---------------------------------------------------------------------- #
# SSH                                                                     #
# ---------------------------------------------------------------------- #


class TestSshConnector:
    def test_connect_execute_disconnect(self, monkeypatch):
        monkeypatch.setattr(
            "app.plugins.installed.official_mikrotik.connector.ssh.ConnectHandler",
            FakeNetmikoHandler,
        )
        connector = SshConnector(_config())
        connector.connect()

        assert len(FakeNetmikoHandler.instances) == 1
        params = FakeNetmikoHandler.instances[0].params
        assert params["device_type"] == "mikrotik_routeros"
        assert params["host"] == "10.0.0.1"
        assert params["port"] == 22  # default when config.port is None
        assert connector.is_connected is True

        output = connector.execute("/system identity print")
        assert output == "echo:/system identity print"
        assert FakeNetmikoHandler.instances[0].commands == ["/system identity print"]

        connector.disconnect()
        assert FakeNetmikoHandler.instances[0].disconnected is True
        assert connector.is_connected is False

    def test_custom_port_used(self, monkeypatch):
        monkeypatch.setattr(
            "app.plugins.installed.official_mikrotik.connector.ssh.ConnectHandler",
            FakeNetmikoHandler,
        )
        SshConnector(_config(port=2222)).connect()
        assert FakeNetmikoHandler.instances[0].params["port"] == 2222

    def test_execute_requires_connection(self):
        connector = SshConnector(_config())
        with pytest.raises(ConnectorConnectionError):
            connector.execute("/system identity print")

    def test_auth_failure_maps_to_auth_error(self, monkeypatch):
        from netmiko.exceptions import NetmikoAuthenticationException

        def _raise(**kwargs):
            raise NetmikoAuthenticationException("authentication failed")

        monkeypatch.setattr(
            "app.plugins.installed.official_mikrotik.connector.ssh.ConnectHandler", _raise
        )
        with pytest.raises(ConnectorAuthenticationError):
            SshConnector(_config()).connect()

    def test_timeout_maps_to_connection_error(self, monkeypatch):
        from netmiko.exceptions import NetmikoTimeoutException

        def _raise(**kwargs):
            raise NetmikoTimeoutException("timed out")

        monkeypatch.setattr(
            "app.plugins.installed.official_mikrotik.connector.ssh.ConnectHandler", _raise
        )
        with pytest.raises(ConnectorConnectionError):
            SshConnector(_config()).connect()

    def test_generic_error_wrapped(self, monkeypatch):
        def _raise(**kwargs):
            raise OSError("network unreachable")

        monkeypatch.setattr(
            "app.plugins.installed.official_mikrotik.connector.ssh.ConnectHandler", _raise
        )
        with pytest.raises(ConnectorConnectionError, match="network unreachable"):
            SshConnector(_config()).connect()


# ---------------------------------------------------------------------- #
# Telnet                                                                  #
# ---------------------------------------------------------------------- #


class TestTelnetConnector:
    def test_default_telnet_port_and_device_type(self, monkeypatch):
        monkeypatch.setattr(
            "app.plugins.installed.official_mikrotik.connector.telnet.ConnectHandler",
            FakeNetmikoHandler,
        )
        connector = TelnetConnector(_config())
        connector.connect()
        params = FakeNetmikoHandler.instances[0].params
        assert params["device_type"] == "mikrotik_routeros_telnet"
        assert params["port"] == 23
        assert connector.is_connected is True

    def test_custom_port_used(self, monkeypatch):
        monkeypatch.setattr(
            "app.plugins.installed.official_mikrotik.connector.telnet.ConnectHandler",
            FakeNetmikoHandler,
        )
        TelnetConnector(_config(port=2323)).connect()
        assert FakeNetmikoHandler.instances[0].params["port"] == 2323

    def test_unsupported_device_type_clear_error(self, monkeypatch):
        def _unsupported_device_type(**kwargs):
            raise ValueError(
                "device_type 'mikrotik_routeros_telnet' not supported by installed netmiko"
            )

        monkeypatch.setattr(
            "app.plugins.installed.official_mikrotik.connector.telnet.ConnectHandler",
            _unsupported_device_type,
        )
        with pytest.raises(ConnectorConnectionError, match="not supported"):
            TelnetConnector(_config()).connect()


# ---------------------------------------------------------------------- #
# Web UI (RouterOS v7 REST)                                               #
# ---------------------------------------------------------------------- #


class FakeRestResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text if text else json.dumps(payload or [])
        self.content = b"[]" if payload is not None else b""
        self.headers = {"Content-Type": "application/json"}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.exceptions.HTTPError(response=self)


class TestRestTranslation:
    def test_overrides_win(self):
        assert (
            WebUiConnector.command_to_rest_path("/system identity print")
            == "system/identity"
        )
        assert (
            WebUiConnector.command_to_rest_path("/system resource print")
            == "system/resource"
        )
        assert WebUiConnector.command_to_rest_path("/interface print") == "interface"

    def test_generic_rule_drops_print(self):
        assert WebUiConnector.command_to_rest_path("/queue tree print") == "queue/tree"

    def test_passthrough_paths_untouched(self):
        assert (
            WebUiConnector.command_to_rest_path("system/resource") == "system/resource"
        )

    def test_empty_command_returns_empty(self):
        assert WebUiConnector.command_to_rest_path("") == ""


class TestWebUiConnector:
    def _session_patch(self, monkeypatch, session):
        monkeypatch.setattr(
            "app.plugins.installed.official_mikrotik.connector.webui.requests.Session",
            lambda: session,
        )

    def test_is_connected_regression_after_connect(self, monkeypatch):
        """Regression: connect() previously never set _connection."""
        requested: list[str] = []

        class FakeSession:
            def get(self, path, timeout=None, verify=None, auth=None):
                requested.append(path)
                return FakeRestResponse(payload=[{"name": "core"}])

        self._session_patch(monkeypatch, FakeSession())
        connector = WebUiConnector(
            _config(port=443, extra={"use_https": True, "verify_ssl": False})
        )
        assert connector.is_connected is False

        connector.connect()
        assert connector.is_connected is True
        assert requested[-1].endswith("/rest/system/resource")

    def test_base_url_http_when_disabled(self):
        connector = WebUiConnector(_config(extra={"use_https": False}))
        assert connector.base_url.startswith("http://")

    def test_execute_translates_cli_and_parses_json(self, monkeypatch):
        calls: list[str] = []

        class FakeSession:
            def get(self, path, timeout=None, verify=None, auth=None):
                calls.append(path)
                return FakeRestResponse(payload=[{"address": "10.0.0.1/24"}])

        self._session_patch(monkeypatch, FakeSession())
        connector = WebUiConnector(_config(port=443))
        connector.connect()

        output = connector.execute("/ip address print")
        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert parsed[0]["address"] == "10.0.0.1/24"
        assert calls[-1].endswith("/rest/ip/address")

    def test_execute_requires_connection(self):
        connector = WebUiConnector(_config(port=443))
        with pytest.raises(ConnectorConnectionError):
            connector.execute("system/resource")

    def test_http_401_maps_to_auth_error(self, monkeypatch):
        class FakeSession:
            def get(self, path, timeout=None, verify=None, auth=None):
                return FakeRestResponse(status_code=401)

        self._session_patch(monkeypatch, FakeSession())
        connector = WebUiConnector(_config(port=443))
        with pytest.raises(ConnectorAuthenticationError):
            connector.connect()

    def test_timeout_maps_to_connection_error(self, monkeypatch):
        import requests

        class FakeSession:
            def get(self, path, timeout=None, verify=None, auth=None):
                raise requests.exceptions.Timeout("timed out")

        self._session_patch(monkeypatch, FakeSession())
        connector = WebUiConnector(_config(port=443))
        with pytest.raises(ConnectorConnectionError):
            connector.connect()

    def test_rest_connector_alias(self):
        assert RestConnector is WebUiConnector
