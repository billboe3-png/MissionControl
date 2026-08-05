"""Mission Control Agent Configuration."""

from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "mission-control-agent"
DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "mission-control-agent"
_FALLBACK_ROOT = Path("C:/MissionControlAgent")


class AgentSettings(BaseSettings):
    """Agent configuration with environment variable overrides."""

    server_url: str = Field(
        default="https://localhost:8000",
        description="Mission Control server URL.",
        alias="MC_SERVER_URL",
    )

    api_key: str = Field(
        default="",
        description="Agent API key for authentication.",
        alias="MC_API_KEY",
    )

    agent_id: int | None = Field(
        default=None,
        description="Registered agent ID.",
        alias="MC_AGENT_ID",
    )

    agent_name: str = Field(
        default="",
        description="Display name for this agent.",
        alias="MC_AGENT_NAME",
    )

    heartbeat_interval: int = Field(
        default=30,
        description="Seconds between heartbeats.",
        alias="MC_HEARTBEAT_INTERVAL",
    )

    inventory_interval: int = Field(
        default=300,
        description="Seconds between inventory collection.",
        alias="MC_INVENTORY_INTERVAL",
    )

    verify_ssl: bool = Field(
        default=True,
        description="Verify TLS certificates.",
        alias="MC_VERIFY_SSL",
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level.",
        alias="MC_LOG_LEVEL",
    )

    log_file: str | None = Field(
        default=None,
        description="Log file path.",
        alias="MC_LOG_FILE",
    )

    config_dir: Path = Field(
        default=DEFAULT_CONFIG_DIR,
        description="Configuration directory.",
        alias="MC_CONFIG_DIR",
    )

    data_dir: Path = Field(
        default=DEFAULT_DATA_DIR,
        description="Data directory for queues and cache.",
        alias="MC_DATA_DIR",
    )

    command_timeout: int = Field(
        default=60,
        description="Default command timeout in seconds.",
        alias="MC_COMMAND_TIMEOUT",
    )

    reconnect_delay: int = Field(
        default=5,
        description="Initial reconnect delay in seconds.",
        alias="MC_RECONNECT_DELAY",
    )

    max_reconnect_delay: int = Field(
        default=300,
        description="Maximum reconnect delay in seconds.",
        alias="MC_MAX_RECONNECT_DELAY",
    )

    offline_buffer_max: int = Field(
        default=1000,
        description="Maximum number of results to buffer offline.",
        alias="MC_OFFLINE_BUFFER_MAX",
    )

    remote_inventory_interval: int = Field(
        default=300,
        description="Seconds between remote target inventory collection.",
        alias="MC_REMOTE_INVENTORY_INTERVAL",
    )

    model_config = {
        "env_prefix": "",
        "extra": "ignore",
        "populate_by_name": True,
    }


def load_config(config_path: str | Path | None = None) -> AgentSettings:
    """Load configuration from file and environment."""
    settings_kwargs: dict = {}

    if config_path is None:
        default_path = DEFAULT_CONFIG_DIR / "config.yaml"
        if default_path.exists():
            config_path = default_path
        else:
            fallback = Path(__file__).resolve().parent.parent / "config.yaml"
            if fallback.exists():
                config_path = fallback
            elif _FALLBACK_ROOT.exists():
                alt = _FALLBACK_ROOT / "config.yaml"
                if alt.exists():
                    config_path = alt

    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            file_config = yaml.safe_load(f) or {}
        settings_kwargs = {
            k: v
            for k, v in file_config.items()
            if v is not None
        }

    # SYSTEM scheduled task fix: force data_dir into a writable, known location
    if "data_dir" not in settings_kwargs:
        settings_kwargs["data_dir"] = _FALLBACK_ROOT / "data"

    return AgentSettings(**settings_kwargs)
