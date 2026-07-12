"""
Remote Provider Tests

Tests for SSH/WinRM providers and the factory.
"""

import pytest

from app.providers.remote.provider_factory import get_remote_provider
from app.providers.remote.ssh_provider import SSHProvider
from app.providers.remote.winrm_provider import WinRMProvider


@pytest.mark.asyncio
async def test_ssh_provider_test_connection():
    """Test SSH provider connection test."""
    provider = SSHProvider()
    result = await provider.test_connection(
        hostname="test.server.local",
        port=22,
        username="testuser",
        password=None,
        ssh_key="fake-key",
        ip_address="10.0.0.1",
    )

    assert result["success"] is True
    assert result["latency_ms"] > 0
    assert "10.0.0.1" in result["message"]
    assert "SSH connection" in result["message"]


@pytest.mark.asyncio
async def test_ssh_provider_execute_command():
    """Test SSH provider command execution."""
    provider = SSHProvider()
    result = await provider.execute_command(
        hostname="test.server.local",
        port=22,
        username="testuser",
        password=None,
        ssh_key="fake-key",
        command="hostname",
        shell="bash",
        ip_address=None,
    )

    assert result["exit_code"] == 0
    assert result["stdout"] == "test.server.local"
    assert result["stderr"] == ""
    assert result["duration_ms"] > 0


@pytest.mark.asyncio
async def test_ssh_provider_execute_custom_command():
    """Test SSH provider with a custom command returns mock output."""
    provider = SSHProvider()
    result = await provider.execute_command(
        hostname="myhost",
        port=22,
        username="user",
        password=None,
        ssh_key=None,
        command="whoami",
        shell="bash",
        ip_address=None,
    )

    assert result["exit_code"] == 0
    assert result["stdout"] == "user"


@pytest.mark.asyncio
async def test_winrm_provider_test_connection():
    """Test WinRM provider connection test."""
    provider = WinRMProvider()
    result = await provider.test_connection(
        hostname="win.server.local",
        port=5985,
        username="admin",
        password="pass",
        ssh_key=None,
        ip_address="10.0.0.2",
    )

    assert result["success"] is True
    assert result["latency_ms"] > 0
    assert "WinRM connection" in result["message"]


@pytest.mark.asyncio
async def test_winrm_provider_execute_command():
    """Test WinRM provider command execution."""
    provider = WinRMProvider()
    result = await provider.execute_command(
        hostname="win.server.local",
        port=5985,
        username="admin",
        password="pass",
        ssh_key=None,
        command="hostname",
        shell="powershell",
        ip_address=None,
    )

    assert result["exit_code"] == 0
    assert "win.server.local" in result["stdout"]
    assert result["stderr"] == ""


def test_factory_returns_ssh_provider():
    """Test factory returns SSHProvider for 'ssh' type."""
    provider = get_remote_provider("ssh")
    assert isinstance(provider, SSHProvider)


def test_factory_returns_winrm_provider():
    """Test factory returns WinRMProvider for 'winrm' type."""
    provider = get_remote_provider("winrm")
    assert isinstance(provider, WinRMProvider)


def test_factory_raises_for_unsupported_type():
    """Test factory raises ValueError for unsupported type."""
    with pytest.raises(ValueError, match="Unsupported connection type"):
        get_remote_provider("telnet")


def test_factory_returns_singleton():
    """Test factory returns the same instance for repeated calls."""
    p1 = get_remote_provider("ssh")
    p2 = get_remote_provider("ssh")
    assert p1 is p2
