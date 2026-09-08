"""Business logic for native MikroTik configuration operations via CLI/Agent relay."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.plugins.installed.official_mikrotik.models import MikroTikServer
from app.plugins.installed.official_mikrotik.repository import MikroTikRepository
from app.plugins.installed.official_mikrotik.service import MikroTikService

logger = logging.getLogger("plugin.mikrotik.config_service")


class MikroTikConfigService:
    """Native configuration management via RouterOS CLI through Agent relay."""

    def __init__(self, repository: MikroTikRepository | None = None) -> None:
        self._repository = repository or MikroTikRepository()
        self._service = MikroTikService()

    # ------------------------------------------------------------------ #
    # Interfaces                                                          #
    # ------------------------------------------------------------------ #

    async def list_interfaces(self, db: Session, server: MikroTikServer) -> list[dict[str, Any]]:
        """List interfaces with configuration details via CLI."""
        result = await self._service.run_command(
            db, server, "/interface print detail without-paging"
        )
        if not result.success:
            raise RuntimeError(result.error or "Failed to fetch interfaces")
        return self._service._map_interfaces(result)

    async def update_interface(
        self, db: Session, server: MikroTikServer, interface_name: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Update interface properties via CLI."""
        allowed_updates = {"disabled", "comment", "name", "mac_address"}
        update_data = {k: v for k, v in payload.items() if k in allowed_updates}
        if not update_data:
            raise ValueError("No valid fields to update")

        commands = []
        if "disabled" in update_data:
            disabled_val = "yes" if update_data["disabled"] else "no"
            commands.append(f"/interface set {interface_name} disabled={disabled_val}")
        if "comment" in update_data:
            comment = update_data["comment"].replace('"', '\\"')
            commands.append(f'/interface set {interface_name} comment="{comment}"')
        if "name" in update_data:
            commands.append(f"/interface set {interface_name} name={update_data['name']}")

        for cmd in commands:
            result = await self._service.run_command(db, server, cmd)
            if not result.success:
                raise RuntimeError(result.error or f"Failed to execute: {cmd}")

        server.status = "online"
        server.last_error = None
        db.commit()
        return {"name": interface_name, "updated": update_data}

    # ------------------------------------------------------------------ #
    # IP Addresses                                                        #
    # ------------------------------------------------------------------ #

    async def list_ip_addresses(self, db: Session, server: MikroTikServer) -> list[dict[str, Any]]:
        """List IP addresses on the server via CLI."""
        result = await self._service.run_command(
            db, server, "/ip address print detail without-paging"
        )
        if not result.success:
            raise RuntimeError(result.error or "Failed to fetch IP addresses")

        addresses = []
        for record in self._service._parse_key_value_output(result.output):
            addresses.append({
                "id": record.get(".id", ""),
                "address": record.get("address", ""),
                "network": record.get("network", ""),
                "interface": record.get("interface", ""),
                "disabled": record.get("disabled", "false").lower() == "true",
                "comment": record.get("comment", ""),
            })
        return addresses

    async def create_ip_address(
        self, db: Session, server: MikroTikServer, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Add a new IP address via CLI."""
        address = payload["address"]
        interface = payload["interface"]
        disabled = payload.get("disabled", False)
        comment = payload.get("comment", "")

        cmd = f"/ip address add address={address} interface={interface}"
        if disabled:
            cmd += " disabled=yes"
        if comment:
            safe_comment = comment.replace('"', '\\"')
            cmd += f' comment="{safe_comment}"'

        result = await self._service.run_command(db, server, cmd)
        if not result.success:
            raise RuntimeError(result.error or f"Failed to add IP address: {cmd}")

        server.status = "online"
        server.last_error = None
        db.commit()
        return {"address": address, "interface": interface}

    async def delete_ip_address(
        self, db: Session, server: MikroTikServer, address_id: str
    ) -> bool:
        """Delete an IP address by its .id via CLI."""
        result = await self._service.run_command(
            db, server, f"/ip address remove {address_id}"
        )
        if not result.success:
            raise RuntimeError(result.error or f"Failed to delete IP address {address_id}")
        return True

    # ------------------------------------------------------------------ #
    # Firewall Rules                                                      #
    # ------------------------------------------------------------------ #

    async def list_firewall_rules(self, db: Session, server: MikroTikServer) -> list[dict[str, Any]]:
        """List firewall rules with editable fields via CLI."""
        result = await self._service.run_command(
            db, server, "/ip firewall filter print detail without-paging"
        )
        if not result.success:
            raise RuntimeError(result.error or "Failed to fetch firewall rules")

        rules = []
        for record in self._service._parse_key_value_output(result.output):
            flags = record.get("_flags", "")
            rules.append({
                "id": record.get(".id", ""),
                "chain": record.get("chain", ""),
                "action": record.get("action", ""),
                "disabled": "X" in flags or record.get("disabled", "false").lower() == "true",
                "comment": record.get("comment", ""),
                "bytes": self._service._detail_int(record.get("bytes")),
                "packets": self._service._detail_int(record.get("packets")),
                "protocol": record.get("protocol", ""),
                "src_address": record.get("src-address", ""),
                "dst_address": record.get("dst-address", ""),
                "src_port": record.get("src-port", ""),
                "dst_port": record.get("dst-port", ""),
                "in_interface": record.get("in-interface", ""),
                "out_interface": record.get("out-interface", ""),
            })
        return rules

    async def create_firewall_rule(
        self, db: Session, server: MikroTikServer, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a new firewall rule via CLI."""
        parts = [
            f"/ip firewall filter add",
            f"chain={payload.get('chain', 'input')}",
            f"action={payload.get('action', 'accept')}",
        ]
        if payload.get("disabled"):
            parts.append("disabled=yes")
        if payload.get("comment"):
            parts.append(f'comment="{payload["comment"].replace(chr(34), chr(39))}"')
        if payload.get("protocol"):
            parts.append(f"protocol={payload['protocol']}")
        if payload.get("src_address"):
            parts.append(f"src-address={payload['src_address']}")
        if payload.get("dst_address"):
            parts.append(f"dst-address={payload['dst_address']}")
        if payload.get("src_port"):
            parts.append(f"src-port={payload['src_port']}")
        if payload.get("dst_port"):
            parts.append(f"dst-port={payload['dst_port']}")
        if payload.get("in_interface"):
            parts.append(f"in-interface={payload['in_interface']}")
        if payload.get("out_interface"):
            parts.append(f"out-interface={payload['out_interface']}")

        cmd = " ".join(parts)
        result = await self._service.run_command(db, server, cmd)
        if not result.success:
            raise RuntimeError(result.error or f"Failed to create firewall rule: {cmd}")

        return {"created": payload, "output": result.output}

    async def update_firewall_rule(
        self, db: Session, server: MikroTikServer, rule_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing firewall rule via CLI."""
        allowed_fields = {
            "chain", "action", "disabled", "comment", "protocol",
            "src-address", "dst-address", "src-port", "dst-port",
            "in-interface", "out-interface",
        }
        update_data = {k: v for k, v in payload.items() if k in allowed_fields}
        if not update_data:
            raise ValueError("No valid fields to update")

        parts = [f"/ip firewall filter set {rule_id}"]
        for key, value in update_data.items():
            if key == "disabled":
                parts.append("disabled=yes" if value else "disabled=no")
            elif key == "comment":
                parts.append(f'comment="{str(value).replace(chr(34), chr(39))}"')
            else:
                parts.append(f"{key}={value}")

        cmd = " ".join(parts)
        result = await self._service.run_command(db, server, cmd)
        if not result.success:
            raise RuntimeError(result.error or f"Failed to update firewall rule {rule_id}")

        return {"id": rule_id, "updated": update_data}

    async def delete_firewall_rule(
        self, db: Session, server: MikroTikServer, rule_id: str
    ) -> bool:
        """Delete a firewall rule via CLI."""
        result = await self._service.run_command(
            db, server, f"/ip firewall filter remove {rule_id}"
        )
        if not result.success:
            raise RuntimeError(result.error or f"Failed to delete firewall rule {rule_id}")
        return True

    # ------------------------------------------------------------------ #
    # DHCP Leases                                                         #
    # ------------------------------------------------------------------ #

    async def list_dhcp_leases(self, db: Session, server: MikroTikServer) -> list[dict[str, Any]]:
        """List DHCP leases via CLI."""
        result = await self._service.run_command(
            db, server, "/ip dhcp-server lease print detail without-paging"
        )
        if not result.success:
            raise RuntimeError(result.error or "Failed to fetch DHCP leases")

        leases = []
        for record in self._service._parse_key_value_output(result.output):
            leases.append({
                "id": record.get(".id", ""),
                "address": record.get("address", ""),
                "mac_address": record.get("mac-address", ""),
                "host_name": record.get("host-name", ""),
                "status": record.get("status", ""),
                "expires_after": record.get("expires-after", ""),
            })
        return leases

    # ------------------------------------------------------------------ #
    # System Configuration                                                #
    # ------------------------------------------------------------------ #

    async def get_system_config(self, db: Session, server: MikroTikServer) -> dict[str, Any]:
        """Get system configuration via CLI."""
        config = {}

        identity_result = await self._service.run_command(db, server, "/system identity print")
        if identity_result.success:
            records = self._service._parse_key_value_output(identity_result.output)
            if records:
                config["identity"] = records[0].get("name", "")

        routerboard_result = await self._service.run_command(
            db, server, "/system routerboard print"
        )
        if routerboard_result.success:
            records = self._service._parse_key_value_output(routerboard_result.output)
            if records:
                config["routerboard"] = records[0]

        return config

    async def update_system_config(
        self, db: Session, server: MikroTikServer, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Update system configuration via CLI."""
        if "identity" in payload:
            cmd = f'/system identity set name="{str(payload["identity"]).replace(chr(34), chr(39))}"'
            result = await self._service.run_command(db, server, cmd)
            if not result.success:
                raise RuntimeError(result.error or "Failed to update identity")

        if "routerboard" in payload:
            rb = payload["routerboard"]
            if rb.get("routerboard"):
                cmd = f"/system routerboard set routerboard={rb['routerboard']}"
                result = await self._service.run_command(db, server, cmd)
                if not result.success:
                    raise RuntimeError(result.error or "Failed to update routerboard setting")

        return {"updated": payload}
