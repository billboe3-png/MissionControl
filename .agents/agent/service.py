"""Mission Control Agent - Production service management.

Supports Windows Service, systemd, and direct execution modes.
"""

import logging
import os
import platform
import signal
import sys
import time
from typing import Any

logger = logging.getLogger("mc-agent")


class AgentService:
    """Wraps MissionControlAgent as a manageable service."""

    SHUTDOWN_TIMEOUT = 30

    def __init__(self, config: Any) -> None:
        self.config = config
        self._start_time: float = 0.0
        self._state = "stopped"
        self._agent: Any = None
        self._shutdown_event: Any = None
        self._setup_signal_handlers()

    def start(self) -> None:
        """Start the agent as a background service."""
        from agent.edge_core import EdgeCore

        logger.info("Edge service starting...")
        self._state = "starting"
        self._start_time = time.monotonic()
        self._state = "running"
        logger.info("Edge service started")

        import asyncio

        self._agent = EdgeCore(self.config)

        try:
            asyncio.run(self._agent.start())
        except KeyboardInterrupt:
            logger.info("Interrupted")
        except Exception as e:
            self._state = "error"
            logger.error("Edge agent failed: %s", e)
            raise

    def stop(self) -> None:
        """Graceful shutdown with timeout."""
        if self._state == "stopped":
            return

        logger.info("Service stopping (timeout=%ds)...", self.SHUTDOWN_TIMEOUT)
        self._state = "stopping"

        if self._agent is not None:
            import asyncio

            try:
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(
                        asyncio.wait_for(
                            self._agent.stop(), timeout=self.SHUTDOWN_TIMEOUT
                        )
                    )
                except TimeoutError:
                    logger.warning(
                        "Agent did not stop within %ds, forcing", self.SHUTDOWN_TIMEOUT
                    )
                finally:
                    loop.close()
            except Exception as e:
                logger.warning("Error during agent stop: %s", e)

        self._state = "stopped"
        logger.info("Service stopped")

    def restart(self) -> None:
        """Stop then start."""
        self.stop()
        self.start()

    def get_status(self) -> dict[str, Any]:
        """Return service status."""
        uptime = 0.0
        if self._start_time > 0 and self._state in ("running", "stopping"):
            uptime = time.monotonic() - self._start_time

        return {
            "version": self._get_version(),
            "uptime": uptime,
            "state": self._state,
            "pid": os.getpid(),
        }

    def install_windows_service(self) -> None:
        """Register as a Windows Service."""
        if platform.system() != "Windows":
            logger.warning("Windows service install requested on non-Windows OS")
            return

        try:
            import win32serviceutil

            win32serviceutil.InstallService()
            logger.info("Windows service installed")
        except ImportError:
            logger.error(
                "pywin32 is not installed. Install it with: pip install pywin32"
            )
        except Exception as e:
            logger.error("Failed to install Windows service: %s", e)

    def install_systemd(self) -> None:
        """Write systemd unit file."""
        if platform.system() != "Linux":
            logger.warning("systemd install requested on non-Linux OS")
            return

        executable = sys.executable or "python3"
        working_dir = os.getcwd()

        unit_content = f"""[Unit]
Description=Mission Control Agent
After=network.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={executable} -m agent
WorkingDirectory={working_dir}
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

Environment=MC_SERVER_URL={self.config.server_url if hasattr(self.config, "server_url") else ""}
Environment=MC_LOG_LEVEL={self.config.log_level if hasattr(self.config, "log_level") else "INFO"}

[Install]
WantedBy=multi-user.target
"""

        unit_path = "/etc/systemd/system/mc-edge-agent.service"
        try:
            with open(unit_path, "w") as f:
                f.write(unit_content)
            logger.info("systemd unit written to %s", unit_path)
            logger.info(
                "Run: systemctl daemon-reload && systemctl enable --now mc-edge-agent"
            )
        except PermissionError:
            logger.error("Permission denied writing %s. Run as root.", unit_path)
        except OSError as e:
            logger.error("Failed to write systemd unit: %s", e)

    def _setup_signal_handlers(self) -> None:
        """Register SIGTERM, SIGINT, SIGHUP."""
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self._on_signal)
        if hasattr(signal, "SIGINT"):
            signal.signal(signal.SIGINT, self._on_signal)
        if hasattr(signal, "SIGHUP"):
            signal.signal(signal.SIGHUP, self._on_signal)

    def _on_signal(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        sig_name = (
            signal.Signals(signum).name if hasattr(signal, "Signals") else str(signum)
        )
        logger.info("Received signal %s, initiating shutdown", sig_name)
        self.stop()

    def _get_version(self) -> str:
        try:
            from agent import __version__

            return __version__
        except ImportError:
            return "unknown"
