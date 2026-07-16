"""
Mission Control Automation Provider Factory

Singleton factory that returns the correct provider based
on the execution backend type.

Sprint 2.8 - Automation & Playbooks.
"""

import logging

from app.providers.automation.base_provider import AutomationProvider
from app.providers.automation.bash_provider import BashAutomationProvider
from app.providers.automation.http_provider import HTTPAutomationProvider
from app.providers.automation.powershell_provider import PowerShellAutomationProvider
from app.providers.automation.ssh_provider import SSHAutomationProvider
from app.providers.automation.winrm_provider import WinRMAutomationProvider
from app.providers.automation.agent_provider import AgentAutomationProvider
from app.providers.automation.hyperv_provider import HyperVAutomationProvider
from app.providers.automation.proxmox_provider import ProxmoxAutomationProvider

logger = logging.getLogger(__name__)

_providers: dict[str, AutomationProvider] = {}


def get_automation_provider(provider_name: str) -> AutomationProvider:
    """
    Return the correct provider based on name.

    Supported providers:
    - 'bash' -> BashAutomationProvider
    - 'powershell' -> PowerShellAutomationProvider
    - 'http' -> HTTPAutomationProvider
    - 'ssh' -> SSHAutomationProvider
    - 'winrm' -> WinRMAutomationProvider
    - 'agent' -> AgentAutomationProvider
    - 'hyperv' -> HyperVAutomationProvider
    - 'proxmox' -> ProxmoxAutomationProvider

    Raises ValueError for unsupported provider types.
    """
    global _providers

    if provider_name in _providers:
        return _providers[provider_name]

    provider_map: dict[str, type[AutomationProvider]] = {
        "bash": BashAutomationProvider,
        "powershell": PowerShellAutomationProvider,
        "http": HTTPAutomationProvider,
        "ssh": SSHAutomationProvider,
        "winrm": WinRMAutomationProvider,
        "agent": AgentAutomationProvider,
        "hyperv": HyperVAutomationProvider,
        "proxmox": ProxmoxAutomationProvider,
    }

    cls = provider_map.get(provider_name)
    if cls is None:
        raise ValueError(
            f"Unsupported automation provider: {provider_name}. "
            f"Supported: {', '.join(provider_map.keys())}"
        )

    provider = cls()
    _providers[provider_name] = provider
    logger.info(
        "Created singleton %s", cls.__name__
    )
    return provider


def get_all_providers() -> dict[str, AutomationProvider]:
    """Return all available providers (creates them if needed)."""
    for name in [
        "bash",
        "powershell",
        "http",
        "ssh",
        "winrm",
        "agent",
        "hyperv",
        "proxmox",
    ]:
        get_automation_provider(name)
    return dict(_providers)
