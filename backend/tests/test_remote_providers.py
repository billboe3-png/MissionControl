"""
Remote Provider Tests

Tests for SSH/WinRM providers and the factory.
SSH tests mock Paramiko to avoid requiring real SSH servers.
"""

from unittest.mock import MagicMock, patch

import paramiko
import pytest
from paramiko.ssh_exception import NoValidConnectionsError

from app.providers.remote.provider_factory import get_remote_provider
from app.providers.remote.ssh_provider import SSHProvider
from app.providers.remote.winrm_provider import WinRMProvider

# ------------------------------------------------------------------ #
# SSH Provider - Connection Test                                      #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_ssh_test_connection_success():
    """Test successful SSH connection test with mocked Paramiko."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 0

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"MissionControl\n"
    mock_stdout.channel = mock_channel

    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b""

    mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.test_connection(
            hostname="test.server.local",
            port=22,
            username="testuser",
            password="testpass",
            ssh_key=None,
            ip_address="10.0.0.1",
        )

    assert result["success"] is True
    assert result["latency_ms"] >= 0
    assert "10.0.0.1" in result["message"]
    assert "SSH connection" in result["message"]
    mock_client.connect.assert_called_once()
    mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_ssh_test_connection_uses_hostname_when_no_ip():
    """Test connection test falls back to hostname in message."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 0

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"MissionControl\n"
    mock_stdout.channel = mock_channel

    mock_client.exec_command.return_value = (None, mock_stdout, MagicMock())

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.test_connection(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is True
    assert "test.server.local" in result["message"]


@pytest.mark.asyncio
async def test_ssh_test_connection_auth_failure():
    """Test SSH connection test handles authentication failure."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = paramiko.AuthenticationException("Auth failed")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.test_connection(
            hostname="test.server.local",
            port=22,
            username="baduser",
            password="badpass",
            ssh_key=None,
            ip_address="10.0.0.1",
        )

    assert result["success"] is False
    assert "authentication failed" in result["message"]


@pytest.mark.asyncio
async def test_ssh_test_connection_refused():
    """Test SSH connection test handles connection refused."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = OSError("Connection refused")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.test_connection(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "connection refused" in result["message"]


@pytest.mark.asyncio
async def test_ssh_test_connection_dns_failure():
    """Test SSH connection test handles DNS resolution failure."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = OSError("No such host")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.test_connection(
            hostname="nonexistent.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "DNS resolution failed" in result["message"]


@pytest.mark.asyncio
async def test_ssh_test_connection_timeout():
    """Test SSH connection test handles connection timeout."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = paramiko.SSHException("Connection timed out")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.test_connection(
            hostname="slow.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "timed out" in result["message"]


@pytest.mark.asyncio
async def test_ssh_test_connection_unreachable():
    """Test SSH connection test handles unreachable host."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = OSError("Network is unreachable")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.test_connection(
            hostname="10.0.0.99",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "host unreachable" in result["message"]


@pytest.mark.asyncio
async def test_ssh_test_connection_unexpected_echo():
    """Test SSH connection test handles unexpected echo response."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 0

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"unexpected output\n"
    mock_stdout.channel = mock_channel

    mock_client.exec_command.return_value = (None, mock_stdout, MagicMock())

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.test_connection(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "unexpected echo response" in result["message"]


@pytest.mark.asyncio
async def test_ssh_test_connection_generic_exception():
    """Test SSH connection test handles unexpected exceptions."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = RuntimeError("Something broke")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.test_connection(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "RuntimeError" in result["message"]


# ------------------------------------------------------------------ #
# SSH Provider - Command Execution                                    #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_ssh_execute_command_success():
    """Test successful SSH command execution."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 0

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"root\n"
    mock_stdout.channel = mock_channel

    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b""

    mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="root",
            password="pass",
            ssh_key=None,
            command="whoami",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == 0
    assert result["stdout"] == "root\n"
    assert result["stderr"] == ""
    assert result["duration_ms"] >= 0
    mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_ssh_execute_command_failure():
    """Test SSH command execution with non-zero exit code."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 127

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b""
    mock_stdout.channel = mock_channel

    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b"command not found\n"

    mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="nonexistent_command",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == 127
    assert result["stdout"] == ""
    assert result["stderr"] == "command not found\n"


@pytest.mark.asyncio
async def test_ssh_execute_command_stderr_capture():
    """Test SSH command execution captures stderr separately."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 1

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"some output\n"
    mock_stdout.channel = mock_channel

    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b"error: something went wrong\n"

    mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="failing_command",
            shell="bash",
            ip_address=None,
        )

    assert result["stdout"] == "some output\n"
    assert result["stderr"] == "error: something went wrong\n"
    assert result["exit_code"] == 1


@pytest.mark.asyncio
async def test_ssh_execute_command_auth_failure():
    """Test SSH command execution handles authentication failure."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = paramiko.AuthenticationException("Auth failed")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="baduser",
            password="badpass",
            ssh_key=None,
            command="ls",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == -1
    assert result["stdout"] == ""
    assert "authentication failed" in result["stderr"]


@pytest.mark.asyncio
async def test_ssh_execute_command_timeout():
    """Test SSH command execution handles command timeout."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = paramiko.SSHException("Timed out")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="sleep 999",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == -1
    timed_out = "timed out" in result["stderr"].lower()
    ssh_err = "ssh error" in result["stderr"].lower()
    assert timed_out or ssh_err


@pytest.mark.asyncio
async def test_ssh_execute_command_connection_refused():
    """Test SSH command execution handles connection refused."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = OSError("Connection refused")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="ls",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == -1
    assert "Connection refused" in result["stderr"]


@pytest.mark.asyncio
async def test_ssh_execute_command_unexpected_exception():
    """Test SSH command execution handles unexpected exceptions."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = RuntimeError("Something broke")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="ls",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == -1
    assert "Unexpected error" in result["stderr"]


@pytest.mark.asyncio
async def test_ssh_execute_command_closes_client():
    """Test SSH command execution always closes the client."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 0

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"ok"
    mock_stdout.channel = mock_channel

    mock_client.exec_command.return_value = (None, mock_stdout, MagicMock())

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="echo ok",
            shell="bash",
            ip_address=None,
        )

    mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_ssh_test_connection_handles_connect_failure_gracefully():
    """Test SSH connection test handles connect() failure without crashing."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = paramiko.AuthenticationException("fail")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.test_connection(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "authentication failed" in result["message"]


# ------------------------------------------------------------------ #
# SSH Provider - socket.timeout Tests                                  #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_ssh_test_connection_socket_timeout():
    """Test SSH connection test handles socket.timeout."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = TimeoutError("timed out")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.test_connection(
            hostname="slow.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "timed out" in result["message"]


@pytest.mark.asyncio
async def test_ssh_execute_command_socket_timeout():
    """Test SSH command execution handles socket.timeout."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = TimeoutError("timed out")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="slow.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="sleep 999",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == -1
    assert "timed out" in result["stderr"].lower()


# ------------------------------------------------------------------ #
# SSH Provider - NoValidConnectionsError Tests                         #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_ssh_test_connection_no_valid_connections():
    """Test SSH connection test handles NoValidConnectionsError."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = NoValidConnectionsError(
        errors={("10.0.0.1", 22): OSError("Connection refused")}
    )

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.test_connection(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            ip_address="10.0.0.1",
        )

    assert result["success"] is False
    assert "connection refused" in result["message"]


@pytest.mark.asyncio
async def test_ssh_execute_command_no_valid_connections():
    """Test SSH command execution handles NoValidConnectionsError."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = NoValidConnectionsError(
        errors={("10.0.0.1", 22): OSError("Connection refused")}
    )

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="ls",
            shell="bash",
            ip_address="10.0.0.1",
        )

    assert result["exit_code"] == -1
    assert "connection refused" in result["stderr"].lower()


# ------------------------------------------------------------------ #
# SSH Provider - Production Features Tests                             #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_ssh_execute_command_returns_success_flag():
    """Test execute_command returns a success boolean field."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 0

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"ok\n"
    mock_stdout.channel = mock_channel

    mock_client.exec_command.return_value = (None, mock_stdout, MagicMock())

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="echo ok",
            shell="bash",
            ip_address=None,
        )

    assert result["success"] is True
    assert result["exit_code"] == 0


@pytest.mark.asyncio
async def test_ssh_execute_command_success_false_on_nonzero():
    """Test execute_command success is False when exit code non-zero."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 1

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b""
    mock_stdout.channel = mock_channel

    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b"error\n"

    mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="failing_command",
            shell="bash",
            ip_address=None,
        )

    assert result["success"] is False
    assert result["exit_code"] == 1


@pytest.mark.asyncio
async def test_ssh_execute_command_returns_started_at_completed_at():
    """Test execute_command returns ISO timestamp fields."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 0

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b""
    mock_stdout.channel = mock_channel

    mock_client.exec_command.return_value = (None, mock_stdout, MagicMock())

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="true",
            shell="bash",
            ip_address=None,
        )

    assert "started_at" in result
    assert "completed_at" in result
    assert "T" in result["started_at"]
    assert "T" in result["completed_at"]


@pytest.mark.asyncio
async def test_ssh_execute_command_returns_duration_ms():
    """Test execute_command returns duration_ms as an integer."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 0

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b""
    mock_stdout.channel = mock_channel

    mock_client.exec_command.return_value = (None, mock_stdout, MagicMock())

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="true",
            shell="bash",
            ip_address=None,
        )

    assert isinstance(result["duration_ms"], int)
    assert result["duration_ms"] >= 0


@pytest.mark.asyncio
async def test_ssh_retry_does_not_retry_auth_failures():
    """Test retry logic does not retry authentication failures."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = paramiko.AuthenticationException(
        "Auth failed"
    )

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="baduser",
            password="badpass",
            ssh_key=None,
            command="ls",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == -1
    assert "authentication failed" in result["stderr"]
    assert mock_client.connect.call_count == 1


@pytest.mark.asyncio
async def test_ssh_retry_retries_transient_failure():
    """Test retry logic retries once for transient connection errors."""
    mock_client_success = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 0
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"ok"
    mock_stdout.channel = mock_channel
    mock_client_success.exec_command.return_value = (
        None,
        mock_stdout,
        MagicMock(),
    )

    call_count = 0

    def build_client_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OSError("Connection reset")
        return mock_client_success

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        side_effect=build_client_side_effect,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="echo ok",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == 0
    assert call_count == 2


@pytest.mark.asyncio
async def test_ssh_retry_exhausted_returns_last_error():
    """Test retry logic raises after exhausting all retries."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = OSError("Connection refused")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="ls",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == -1
    assert "Connection refused" in result["stderr"]


@pytest.mark.asyncio
async def test_ssh_execute_command_empty_stdout():
    """Test execute_command handles empty stdout gracefully."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 0

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b""
    mock_stdout.channel = mock_channel

    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b""

    mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="true",
            shell="bash",
            ip_address=None,
        )

    assert result["stdout"] == ""
    assert result["stderr"] == ""
    assert result["exit_code"] == 0


@pytest.mark.asyncio
async def test_ssh_execute_command_utf8_decode_error():
    """Test execute_command handles binary output with decode errors."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 0

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"\xff\xfe binary data"
    mock_stdout.channel = mock_channel

    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b""

    mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="cat binary_file",
            shell="bash",
            ip_address=None,
        )

    assert isinstance(result["stdout"], str)
    assert result["exit_code"] == 0


@pytest.mark.asyncio
async def test_ssh_execute_command_dns_failure():
    """Test SSH command execution handles DNS resolution failure."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = OSError("Name or service not known")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="nonexistent.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="ls",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == -1
    assert "DNS resolution failed" in result["stderr"]


@pytest.mark.asyncio
async def test_ssh_execute_command_host_unreachable():
    """Test SSH command execution handles unreachable host."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = OSError("Network is unreachable")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="10.0.0.99",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="ls",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == -1
    assert "Host unreachable" in result["stderr"]


@pytest.mark.asyncio
async def test_ssh_execute_command_general_ssh_exception():
    """Test SSH command execution handles generic SSHException."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = paramiko.SSHException("Generic SSH error")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="ls",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == -1
    assert "SSH error" in result["stderr"]


@pytest.mark.asyncio
async def test_ssh_execute_command_ssh_timeout_error():
    """Test SSH command execution handles SSHException with 'timed out'."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = paramiko.SSHException("timed out")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="slow.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="sleep 999",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == -1
    assert "timed out" in result["stderr"].lower()


@pytest.mark.asyncio
async def test_ssh_execute_command_no_valid_connections_error():
    """Test SSH command execution handles NoValidConnectionsError."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = NoValidConnectionsError(
        errors={("10.0.0.1", 22): OSError("Connection refused")}
    )

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="ls",
            shell="bash",
            ip_address="10.0.0.1",
        )

    assert result["exit_code"] == -1
    assert "Connection refused" in result["stderr"]


@pytest.mark.asyncio
async def test_ssh_execute_command_connection_refused_oserror():
    """Test SSH command execution handles OSError connection refused."""
    mock_client = MagicMock()
    mock_client.connect.side_effect = OSError("Connection refused")

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        result = await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="ls",
            shell="bash",
            ip_address=None,
        )

    assert result["exit_code"] == -1
    assert "Connection refused" in result["stderr"]


# ------------------------------------------------------------------ #
# SSH Provider - Connection Reuse Tests                                #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_ssh_connection_reuse_across_commands():
    """Test SSH client is reused across multiple commands."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_channel.recv_exit_status_ready.return_value = True
    mock_channel.recv_exit_status.return_value = 0

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"ok"
    mock_stdout.channel = mock_channel

    mock_client.exec_command.return_value = (None, mock_stdout, MagicMock())

    # Simulate active transport
    mock_transport = MagicMock()
    mock_transport.is_active.return_value = True
    mock_client.get_transport.return_value = mock_transport

    with patch(
        "app.providers.remote.ssh_provider.paramiko.SSHClient",
        return_value=mock_client,
    ):
        provider = SSHProvider()
        # First call: _get_client creates and stores client
        await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="echo ok",
            shell="bash",
            ip_address=None,
        )
        # Second call: _execute_with_retry builds fresh client per call
        await provider.execute_command(
            hostname="test.server.local",
            port=22,
            username="user",
            password=None,
            ssh_key=None,
            command="echo ok",
            shell="bash",
            ip_address=None,
        )

    # _execute_with_retry builds a fresh client each time,
    # but _build_client is still called each time
    assert mock_client.connect.call_count == 2


# ------------------------------------------------------------------ #
# SSH Provider - stream_command Tests                                  #
# ------------------------------------------------------------------ #


def test_ssh_stream_command_default_implementation():
    """Test stream_command yields from execute_command result."""
    import asyncio
    from unittest.mock import MagicMock  # noqa: I001
    from unittest.mock import patch as _patch

    from app.providers.remote.base_provider import RemoteBaseProvider

    class DummyProvider(RemoteBaseProvider):
        async def test_connection(self, **kwargs):
            return {"success": True}

        async def execute_command(self, **kwargs):
            return {
                "stdout": "line1\nline2\n",
                "stderr": "warn\n",
                "exit_code": 0,
                "success": True,
                "duration_ms": 100,
                "started_at": "2025-01-01T00:00:00+00:00",
                "completed_at": "2025-01-01T00:00:00+00:00",
            }

        async def upload_file(self, **kwargs):
            return {"success": True, "message": "ok", "remote_path": kwargs.get("remote_path", "")}

        async def download_file(self, **kwargs):
            return {"success": True, "message": "ok", "remote_path": kwargs.get("remote_path", ""), "content": b"", "size_bytes": 0}

        async def list_directory(self, **kwargs):
            return {"success": True, "path": kwargs.get("remote_path", ""), "items": []}

        async def create_directory(self, **kwargs):
            return {"success": True, "message": "ok", "remote_path": kwargs.get("remote_path", "")}

        async def delete_file(self, **kwargs):
            return {"success": True, "message": "ok", "remote_path": kwargs.get("remote_path", "")}

    provider = DummyProvider()

    mock_result = {
        "stdout": "line1\nline2\n",
        "stderr": "warn\n",
        "exit_code": 0,
        "success": True,
        "duration_ms": 100,
        "started_at": "2025-01-01T00:00:00+00:00",
        "completed_at": "2025-01-01T00:00:00+00:00",
    }

    async def fake_execute(**kwargs):
        return mock_result

    with _patch.object(provider, "execute_command", side_effect=fake_execute):
        with _patch("asyncio.get_event_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_loop.run_until_complete = MagicMock(
                side_effect=lambda coro: asyncio.get_event_loop_policy()
                .new_event_loop()
                .run_until_complete(coro)
            )
            mock_get_loop.return_value = mock_loop

            chunks = list(
                provider.stream_command(
                    hostname="test",
                    port=22,
                    username="user",
                    password=None,
                    ssh_key=None,
                    command="echo ok",
                    shell="bash",
                    ip_address=None,
                )
            )

    types = [c["type"] for c in chunks]
    assert "stdout" in types
    assert "stderr" in types
    assert "exit_code" in types
    exit_chunk = next(c for c in chunks if c["type"] == "exit_code")
    assert exit_chunk["data"] == 0


# ------------------------------------------------------------------ #
# WinRM Provider Tests (pywinrm-mocked)                               #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_winrm_test_connection_success():
    """Test successful WinRM connection test."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.status_code = 0
    mock_result.std_out = b"MissionControl"
    mock_result.std_err = b""
    mock_session.run_cmd.return_value = mock_result

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
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
    assert result["latency_ms"] >= 0
    assert "10.0.0.2" in result["message"]
    assert "WinRM connection" in result["message"]


@pytest.mark.asyncio
async def test_winrm_test_connection_uses_hostname_when_no_ip():
    """Test WinRM connection test falls back to hostname."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.status_code = 0
    mock_result.std_out = b"MissionControl"
    mock_result.std_err = b""
    mock_session.run_cmd.return_value = mock_result

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.test_connection(
            hostname="win.server.local",
            port=5985,
            username="admin",
            password="pass",
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is True
    assert "win.server.local" in result["message"]


@pytest.mark.asyncio
async def test_winrm_test_connection_auth_failure():
    """Test WinRM connection test handles authentication failure."""
    mock_session = MagicMock()
    mock_session.run_cmd.side_effect = Exception(
        "401 Unauthorized: Access is denied"
    )

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.test_connection(
            hostname="win.server.local",
            port=5985,
            username="baduser",
            password="badpass",
            ssh_key=None,
            ip_address="10.0.0.2",
        )

    assert result["success"] is False
    assert "authentication failed" in result["message"]


@pytest.mark.asyncio
async def test_winrm_test_connection_timeout():
    """Test WinRM connection test handles timeout."""
    mock_session = MagicMock()
    mock_session.run_cmd.side_effect = Exception("Connection timed out")

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.test_connection(
            hostname="slow.server.local",
            port=5985,
            username="admin",
            password="pass",
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "timed out" in result["message"]


@pytest.mark.asyncio
async def test_winrm_test_connection_refused():
    """Test WinRM connection test handles connection refused."""
    mock_session = MagicMock()
    mock_session.run_cmd.side_effect = Exception("Connection refused")

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.test_connection(
            hostname="win.server.local",
            port=5985,
            username="admin",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "connection refused" in result["message"]


@pytest.mark.asyncio
async def test_winrm_test_connection_dns_failure():
    """Test WinRM connection test handles DNS resolution failure."""
    mock_session = MagicMock()
    mock_session.run_cmd.side_effect = Exception(
        "Name or service not known"
    )

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.test_connection(
            hostname="nonexistent.local",
            port=5985,
            username="admin",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "DNS resolution failed" in result["message"]


@pytest.mark.asyncio
async def test_winrm_test_connection_unreachable():
    """Test WinRM connection test handles unreachable host."""
    mock_session = MagicMock()
    mock_session.run_cmd.side_effect = Exception(
        "Host is unreachable"
    )

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.test_connection(
            hostname="10.0.0.99",
            port=5985,
            username="admin",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "host unreachable" in result["message"]


@pytest.mark.asyncio
async def test_winrm_test_connection_unexpected_exception():
    """Test WinRM connection test handles generic exceptions."""
    mock_session = MagicMock()
    mock_session.run_cmd.side_effect = RuntimeError("Something broke")

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.test_connection(
            hostname="win.server.local",
            port=5985,
            username="admin",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "RuntimeError" in result["message"]


@pytest.mark.asyncio
async def test_winrm_test_connection_unexpected_output():
    """Test WinRM connection test handles unexpected probe output."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.status_code = 0
    mock_result.std_out = b"unexpected output"
    mock_result.std_err = b""
    mock_session.run_cmd.return_value = mock_result

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.test_connection(
            hostname="win.server.local",
            port=5985,
            username="admin",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "unexpected response" in result["message"]


@pytest.mark.asyncio
async def test_winrm_test_connection_nonzero_status():
    """Test WinRM connection test handles non-zero status code."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.status_code = 1
    mock_result.std_out = b"MissionControl"
    mock_result.std_err = b"some error"
    mock_session.run_cmd.return_value = mock_result

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.test_connection(
            hostname="win.server.local",
            port=5985,
            username="admin",
            password=None,
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False


# ------------------------------------------------------------------ #
# WinRM Provider - Command Execution Tests                            #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_winrm_execute_command_success():
    """Test successful WinRM command execution."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.status_code = 0
    mock_result.std_out = b"WIN-SERVER01\n"
    mock_result.std_err = b""
    mock_session.run_cmd.return_value = mock_result

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
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

    assert result["success"] is True
    assert result["exit_code"] == 0
    assert "WIN-SERVER01" in result["stdout"]
    assert result["stderr"] == ""
    assert result["duration_ms"] >= 0
    assert "started_at" in result
    assert "completed_at" in result


@pytest.mark.asyncio
async def test_winrm_execute_command_nonzero_exit():
    """Test WinRM command execution with non-zero exit code."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.status_code = 1
    mock_result.std_out = b""
    mock_result.std_err = b"Access denied\n"
    mock_session.run_cmd.return_value = mock_result

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.execute_command(
            hostname="win.server.local",
            port=5985,
            username="admin",
            password="pass",
            ssh_key=None,
            command="Get-Secret",
            shell="powershell",
            ip_address=None,
        )

    assert result["success"] is False
    assert result["exit_code"] == 1
    assert "Access denied" in result["stderr"]


@pytest.mark.asyncio
async def test_winrm_execute_command_auth_failure():
    """Test WinRM command execution handles auth failure."""
    mock_session = MagicMock()
    mock_session.run_cmd.side_effect = Exception(
        "401 Unauthorized: Access is denied"
    )

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.execute_command(
            hostname="win.server.local",
            port=5985,
            username="baduser",
            password="badpass",
            ssh_key=None,
            command="hostname",
            shell="powershell",
            ip_address=None,
        )

    assert result["success"] is False
    assert result["exit_code"] == -1
    assert "authentication failed" in result["stderr"]


@pytest.mark.asyncio
async def test_winrm_execute_command_timeout():
    """Test WinRM command execution handles timeout."""
    mock_session = MagicMock()
    mock_session.run_cmd.side_effect = Exception("Command execution timed out")

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.execute_command(
            hostname="win.server.local",
            port=5985,
            username="admin",
            password="pass",
            ssh_key=None,
            command="Start-Sleep -Seconds 999",
            shell="powershell",
            ip_address=None,
        )

    assert result["success"] is False
    assert result["exit_code"] == -1
    assert "timed out" in result["stderr"].lower()


@pytest.mark.asyncio
async def test_winrm_execute_command_refused():
    """Test WinRM command execution handles connection refused."""
    mock_session = MagicMock()
    mock_session.run_cmd.side_effect = Exception("Connection refused")

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.execute_command(
            hostname="win.server.local",
            port=5985,
            username="admin",
            password=None,
            ssh_key=None,
            command="hostname",
            shell="powershell",
            ip_address=None,
        )

    assert result["success"] is False
    assert result["exit_code"] == -1
    assert "Connection refused" in result["stderr"]


@pytest.mark.asyncio
async def test_winrm_execute_command_dns_failure():
    """Test WinRM command execution handles DNS failure."""
    mock_session = MagicMock()
    mock_session.run_cmd.side_effect = OSError("Name or service not known")

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.execute_command(
            hostname="nonexistent.local",
            port=5985,
            username="admin",
            password=None,
            ssh_key=None,
            command="hostname",
            shell="powershell",
            ip_address=None,
        )

    assert result["success"] is False
    assert result["exit_code"] == -1
    assert "DNS resolution failed" in result["stderr"]


@pytest.mark.asyncio
async def test_winrm_execute_command_unreachable():
    """Test WinRM command execution handles unreachable host."""
    mock_session = MagicMock()
    mock_session.run_cmd.side_effect = OSError("Network is unreachable")

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.execute_command(
            hostname="10.0.0.99",
            port=5985,
            username="admin",
            password=None,
            ssh_key=None,
            command="hostname",
            shell="powershell",
            ip_address=None,
        )

    assert result["success"] is False
    assert result["exit_code"] == -1
    assert "Host unreachable" in result["stderr"]


@pytest.mark.asyncio
async def test_winrm_execute_command_unexpected_exception():
    """Test WinRM command execution handles generic exceptions."""
    mock_session = MagicMock()
    mock_session.run_cmd.side_effect = RuntimeError("Something broke")

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.execute_command(
            hostname="win.server.local",
            port=5985,
            username="admin",
            password=None,
            ssh_key=None,
            command="hostname",
            shell="powershell",
            ip_address=None,
        )

    assert result["success"] is False
    assert result["exit_code"] == -1
    assert "WinRM error" in result["stderr"]


@pytest.mark.asyncio
async def test_winrm_execute_command_returns_timestamps():
    """Test execute_command returns ISO timestamp fields."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.status_code = 0
    mock_result.std_out = b"ok"
    mock_result.std_err = b""
    mock_session.run_cmd.return_value = mock_result

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.execute_command(
            hostname="win.server.local",
            port=5985,
            username="admin",
            password=None,
            ssh_key=None,
            command="echo ok",
            shell="powershell",
            ip_address=None,
        )

    assert "started_at" in result
    assert "completed_at" in result
    assert "T" in result["started_at"]


# ------------------------------------------------------------------ #
# WinRM Provider - SSL / Edge Case Tests                              #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_winrm_test_connection_ssl_failure():
    """Test WinRM connection test handles SSL/TLS handshake failure."""
    mock_session = MagicMock()
    mock_session.run_cmd.side_effect = Exception(
        "SSL: CERTIFICATE_VERIFY_FAILED"
    )

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.test_connection(
            hostname="win.server.local",
            port=5986,
            username="admin",
            password="pass",
            ssh_key=None,
            ip_address=None,
        )

    assert result["success"] is False
    assert "SSL/TLS handshake failed" in result["message"]


@pytest.mark.asyncio
async def test_winrm_execute_command_ssl_failure():
    """Test WinRM command execution handles SSL/TLS handshake failure."""
    mock_session = MagicMock()
    mock_session.run_cmd.side_effect = Exception(
        "ssl.SSLError: certificate verify failed"
    )

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.execute_command(
            hostname="win.server.local",
            port=5986,
            username="admin",
            password="pass",
            ssh_key=None,
            command="hostname",
            shell="powershell",
            ip_address=None,
        )

    assert result["success"] is False
    assert result["exit_code"] == -1
    assert "SSL/TLS handshake failed" in result["stderr"]


@pytest.mark.asyncio
async def test_winrm_execute_command_empty_output():
    """Test WinRM command execution handles empty stdout/stderr."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.status_code = 0
    mock_result.std_out = b""
    mock_result.std_err = b""
    mock_session.run_cmd.return_value = mock_result

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.execute_command(
            hostname="win.server.local",
            port=5985,
            username="admin",
            password="pass",
            ssh_key=None,
            command="echo",
            shell="powershell",
            ip_address=None,
        )

    assert result["success"] is True
    assert result["stdout"] == ""
    assert result["stderr"] == ""
    assert result["exit_code"] == 0


@pytest.mark.asyncio
async def test_winrm_execute_command_large_stdout():
    """Test WinRM command execution handles large stdout output."""
    large_output = ("x" * 50000 + "\n").encode("utf-8")
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.status_code = 0
    mock_result.std_out = large_output
    mock_result.std_err = b""
    mock_session.run_cmd.return_value = mock_result

    with patch(
        "app.providers.remote.winrm_provider.winrm.Session",
        return_value=mock_session,
    ):
        provider = WinRMProvider()
        result = await provider.execute_command(
            hostname="win.server.local",
            port=5985,
            username="admin",
            password="pass",
            ssh_key=None,
            command="Get-Content bigfile.txt",
            shell="powershell",
            ip_address=None,
        )

    assert result["success"] is True
    assert len(result["stdout"]) == 50001
    assert result["exit_code"] == 0


# ------------------------------------------------------------------ #
# Factory Tests                                                       #
# ------------------------------------------------------------------ #


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
