"""
D-Link DGS-1210 Service - Business logic and agent coordination
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .models import DLinkSwitch, DLinkRemoteTarget
from .repository import repository
from .relay import execute_plugin_command, rest_api_call

logger = logging.getLogger("plugin.dlink.service")


class DLinkService:
    """Service layer for D-Link switch management."""

    def __init__(self):
        self._repository = repository

    # ---- Switch Management ----

    def get_switch(self, db, switch_id: int) -> Optional[DLinkSwitch]:
        return self._repository.get_switch(db, switch_id)

    def list_switches(self, db, **kwargs) -> List[DLinkSwitch]:
        return self._repository.list_switches(db, **kwargs)

    def count_switches(self, db, **kwargs) -> int:
        return self._repository.count_switches(db, **kwargs)

    def create_switch(self, db, **kwargs) -> DLinkSwitch:
        switch = self._repository.create_switch(db, **kwargs)
        db.commit()
        return switch

    def update_switch(self, db, switch_id: int, **kwargs) -> Optional[DLinkSwitch]:
        switch = self._repository.update_switch(db, switch_id, **kwargs)
        if switch:
            db.commit()
        return switch

    def delete_switch(self, db, switch_id: int) -> bool:
        result = self._repository.delete_switch(db, switch_id)
        if result:
            db.commit()
        return result

    # ---- Remote Target Management ----

    def get_remote_target(self, db, target_id: int) -> Optional[DLinkRemoteTarget]:
        return self._repository.get_remote_target(db, target_id)

    def create_remote_target(self, db, **kwargs) -> DLinkRemoteTarget:
        target = self._repository.create_remote_target(db, **kwargs)
        db.commit()
        return target

    def update_remote_target(self, db, target_id: int, **kwargs) -> Optional[DLinkRemoteTarget]:
        target = self._repository.update_remote_target(db, target_id, **kwargs)
        if target:
            db.commit()
        return target

    def delete_remote_target(self, db, target_id: int) -> bool:
        result = self._repository.delete_remote_target(db, target_id)
        if result:
            db.commit()
        return result

    # ---- CLI Command Execution via Agent ----

    async def execute_cli(self, db, switch_id: int, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute a CLI command on the D-Link switch via agent relay."""
        switch = self.get_switch(db, switch_id)
        if not switch:
            return {"success": False, "error": "Switch not found"}

        if not switch.remote_target_id:
            return {"success": False, "error": "No remote target configured"}

        result = await execute_plugin_command(
            target_id=switch.remote_target_id,
            command="cli",
            params={"command": command, "timeout": timeout},
            namespace="dlink"
        )
        return result

    async def test_connection(self, db, switch_id: int) -> Dict[str, Any]:
        """Test connectivity to the D-Link switch."""
        switch = self.get_switch(db, switch_id)
        if not switch:
            return {"success": False, "error": "Switch not found"}

        if not switch.remote_target_id:
            return {"success": False, "error": "No remote target configured"}

        return await execute_plugin_command(
            target_id=switch.remote_target_id,
            command="test_connection",
            params={},
            namespace="dlink"
        )

    # ---- Inventory Collection ----

    async def collect_inventory(self, db, switch_id: int) -> Dict[str, Any]:
        """Collect full inventory from the D-Link switch."""
        switch = self.get_switch(db, switch_id)
        if not switch:
            return {"success": False, "error": "Switch not found"}

        if not switch.remote_target_id:
            return {"success": False, "error": "No remote target configured"}

        result = await execute_plugin_command(
            target_id=switch.remote_target_id,
            command="collect_inventory",
            params={},
            namespace="dlink"
        )

        if result.get("success") and "inventory" in result:
            inv = result["inventory"]
            # Update switch with collected info
            update_data = {}
            if inv.get("firmware_version"):
                update_data["firmware_version"] = inv["firmware_version"]
            if inv.get("hardware_version"):
                update_data["hardware_version"] = inv["hardware_version"]
            if inv.get("serial_number"):
                update_data["serial_number"] = inv["serial_number"]
            if inv.get("model_name"):
                update_data["model_name"] = inv["model_name"]
            if inv.get("mac_address"):
                update_data["mac_address"] = inv["mac_address"]
            if update_data:
                update_data["last_seen"] = datetime.utcnow()
                update_data["status"] = "online"
                update_data["last_error"] = None
                self._repository.update_switch(db, switch_id, **update_data)
                db.commit()
        else:
            # Mark as offline on failure
            self._repository.update_switch(db, switch_id, status="offline", last_error=result.get("error"))
            db.commit()

        return result

    async def collect_mac_table(self, db, switch_id: int) -> Dict[str, Any]:
        """Collect MAC address table (FDB) from the switch."""
        switch = self.get_switch(db, switch_id)
        if not switch:
            return {"success": False, "error": "Switch not found"}

        if not switch.remote_target_id:
            return {"success": False, "error": "No remote target configured"}

        return await execute_plugin_command(
            target_id=switch.remote_target_id,
            command="get_mac_table",
            params={},
            namespace="dlink"
        )

    async def collect_vlans(self, db, switch_id: int) -> Dict[str, Any]:
        """Collect VLAN configuration from the switch."""
        switch = self.get_switch(db, switch_id)
        if not switch:
            return {"success": False, "error": "Switch not found"}

        if not switch.remote_target_id:
            return {"success": False, "error": "No remote target configured"}

        return await execute_plugin_command(
            target_id=switch.remote_target_id,
            command="get_vlans",
            params={},
            namespace="dlink"
        )

    async def collect_port_vlans(self, db, switch_id: int) -> Dict[str, Any]:
        """Collect per-port VLAN configuration."""
        switch = self.get_switch(db, switch_id)
        if not switch:
            return {"success": False, "error": "Switch not found"}

        if not switch.remote_target_id:
            return {"success": False, "error": "No remote target configured"}

        return await execute_plugin_command(
            target_id=switch.remote_target_id,
            command="get_port_vlans",
            params={},
            namespace="dlink"
        )

    # ---- Configuration Commands ----

    async def configure_port(self, db, switch_id: int, port: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure a port (VLAN, PVID, mode, etc.)."""
        return await self.execute_cli(db, switch_id, f"config ports {port} " + " ".join(
            f"{k} {v}" for k, v in config.items()
        ))

    async def configure_vlan(self, db, switch_id: int, vlan_id: int, name: Optional[str],
                             ports_tagged: Optional[List[int]], ports_untagged: Optional[List[int]]) -> Dict[str, Any]:
        """Configure a VLAN."""
        cmd_parts = [f"create vlan {vlan_id}"]
        if name:
            cmd_parts.append(f"name {name}")
        if ports_tagged:
            cmd_parts.append(f"tagged {' '.join(str(p) for p in ports_tagged)}")
        if ports_untagged:
            cmd_parts.append(f"untagged {' '.join(str(p) for p in ports_untagged)}")
        return await self.execute_cli(db, switch_id, " ".join(cmd_parts))

    # ---- Web UI REST API ----

    async def webui_request(
        self, db, switch_id: int, method: str, path: str,
        body: Optional[Dict] = None, headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make a REST API call to the D-Link switch web UI."""
        switch = self.get_switch(db, switch_id)
        if not switch:
            return {"success": False, "error": "Switch not found"}

        if not switch.remote_target_id:
            return {"success": False, "error": "No remote target configured"}

        return await rest_api_call(
            target_id=switch.remote_target_id,
            method=method,
            path=path,
            body=body,
            headers=headers,
            port=switch.webui_port,
            use_https=switch.webui_use_https
        )


# Singleton instance
dlink_service = DLinkService()