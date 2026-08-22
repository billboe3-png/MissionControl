"""Mission Control Agent - Network Discovery plugin.

Maps network devices to switch ports using:
- ARP/neighbor discovery on local subnets
- SNMPv2 queries to switches (BRIDGE-MIB, LLDP-MIB, CDP-MIB)
- Local interface LLDP/CDP collection where available

All paths go through the agent (Server -> Agent -> Target).
"""

import asyncio
import logging
import re
from datetime import UTC
from typing import Any

from agent.plugin import AgentPlugin

_UTC = UTC

logger = logging.getLogger("mc-agent")


class NetworkDiscoveryPlugin(AgentPlugin):
    """Network topology discovery plugin."""

    name = "network_discovery"
    version = "3.0.0-rc1"
    description = "Network discovery and switch port mapping"
    platform_required = None

    def __init__(self) -> None:
        self._context: dict[str, Any] = {}
        self._community = "public"
        self._subnets: list[str] = []
        self._switch_ips: list[str] = []
        self._snmp_timeout = 3
        self._snmp_retries = 1

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context
        self._community = context.get("snmp_community", "public")
        self._subnets = context.get("subnets", [])
        self._switch_ips = context.get("switch_ips", [])
        self._snmp_timeout = int(context.get("snmp_timeout", 3))
        self._snmp_retries = int(context.get("snmp_retries", 1))
        logger.info(
            "NetworkDiscovery initialized: subnets=%s switches=%s",
            self._subnets,
            self._switch_ips,
        )
        return True

    async def collect_inventory(self) -> dict[str, Any]:
        """Run full discovery and return combined results."""
        devices = []
        switch_topology = []

        # Local ARP/neighbor table
        arp_devices = await self._collect_local_arp()
        devices.extend(arp_devices)

        # SNMP switch queries
        if self._switch_ips:
            for switch_ip in self._switch_ips:
                try:
                    topo = await self._query_switch(switch_ip)
                    switch_topology.append({"switch_ip": switch_ip, "topology": topo})
                except Exception as exc:
                    logger.warning("Switch %s query failed: %s", switch_ip, exc)

        # Combine ARP + switch data
        merged = self._merge_arp_with_switch(devices, switch_topology)

        # Local interface info
        local_ifaces = await self._collect_local_interfaces()

        return {
            "available": True,
            "discovered_at": __import__("datetime").datetime.now(_UTC).isoformat(),
            "devices": merged,
            "local_interfaces": local_ifaces,
            "switch_topology": switch_topology,
        }

    async def execute_command(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute targeted discovery commands."""
        if command == "scan-subnet":
            subnet = args.get("subnet", "")
            if not subnet:
                return {"success": False, "error": "subnet required"}
            devices = await self._arp_scan_subnet(subnet)
            return {"success": True, "devices": devices}

        if command == "query-switch":
            switch_ip = args.get("switch_ip", "")
            if not switch_ip:
                return {"success": False, "error": "switch_ip required"}
            topo = await self._query_switch(switch_ip)
            return {"success": True, "topology": topo}

        if command == "get-local-arp":
            devices = await self._collect_local_arp()
            return {"success": True, "devices": devices}

        return {"success": False, "error": f"Unknown command: {command}"}

    # ------------------------------------------------------------------
    # ARP / neighbor discovery
    # ------------------------------------------------------------------

    async def _collect_local_arp(self) -> list[dict[str, Any]]:
        """Collect ARP/neighbor table from the local host."""
        devices: list[dict[str, Any]] = []

        # Try PowerShell Get-NetNeighbor first (more reliable on Windows)
        try:
            ps_cmd = (
                "Get-NetNeighbor -AddressFamily IPv4 "
                "| Select-Object IPAddress, LinkLayerAddress, InterfaceAlias, State "
                "| ConvertTo-Json -Depth 3"
            )
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-Command", ps_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
            data = self._parse_json(stdout.decode())
            if isinstance(data, dict):
                data = [data]
            for entry in data:
                mac = entry.get("LinkLayerAddress", "")
                if mac:
                    devices.append({
                        "ip": entry.get("IPAddress", ""),
                        "mac": self._normalize_mac(mac),
                        "interface": entry.get("InterfaceAlias", ""),
                        "state": entry.get("State", ""),
                        "source": "arp",
                    })
            return devices
        except Exception as exc:
            logger.debug("Get-NetNeighbor failed, trying arp -a: %s", exc)

        # Fallback: arp -a
        try:
            proc = await asyncio.create_subprocess_exec(
                "arp", "-a",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            devices.extend(self._parse_arp_a(stdout.decode()))
        except Exception as exc:
            logger.warning("arp -a failed: %s", exc)

        return devices

    def _parse_arp_a(self, text: str) -> list[dict[str, Any]]:
        """Parse Windows arp -a output."""
        devices: list[dict[str, Any]] = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("Interface:") or "---" in line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                ip = parts[0]
                mac = parts[1]
                state = parts[2] if len(parts) > 2 else ""
                if re.match(r"\d+\.\d+\.\d+\.\d+", ip) and re.match(
                    r"([0-9a-fA-F]{2}[-:]){5}[0-9a-fA-F]{2}", mac
                ):
                    devices.append({
                        "ip": ip,
                        "mac": self._normalize_mac(mac),
                        "state": state,
                        "source": "arp",
                    })
        return devices

    async def _arp_scan_subnet(self, subnet: str) -> list[dict[str, Any]]:
        """ARP scan a /24 subnet using async ping sweep + arp -a."""
        devices: list[dict[str, Any]] = []
        base = subnet.rsplit(".", 1)[0]
        if not base:
            return devices

        # Fast ping sweep
        ping_procs = []
        for i in range(1, 255):
            ip = f"{base}.{i}"
            ping_procs.append(
                asyncio.create_subprocess_exec(
                    "ping", "-n", "1", "-w", "500", ip,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
            )

        # Wait for all pings (don't fail the whole scan if some time out)
        try:  # noqa: SIM105
            await asyncio.gather(*ping_procs, return_exceptions=True)
        except Exception:
            pass

        # Read ARP cache
        devices = await self._collect_local_arp()
        return [d for d in devices if d.get("ip", "").startswith(base + ".")]

    # ------------------------------------------------------------------
    # SNMP switch queries
    # ------------------------------------------------------------------

    async def _query_switch(self, switch_ip: str) -> list[dict[str, Any]]:
        """Query a switch via SNMPv2 for bridge, LLDP, and CDP data."""
        topology: list[dict[str, Any]] = []

        # Q-BRIDGE-MIB: dot1dTpFdbTable + dot1dBasePortIfIndex
        bridge_ports = await self._snmp_walk(
            switch_ip, "1.3.6.1.2.1.17.7.1.2.2.1.2"  # dot1dTpFdbPort
        )
        fdb_to_port: dict[str, str] = {}
        for mac_oid, port_idx in bridge_ports.items():
            mac = self._oid_to_mac(mac_oid)
            fdb_to_port[mac] = port_idx

        # IF-MIB: ifDescr for port index -> name mapping
        if_descr = await self._snmp_walk(
            switch_ip, "1.3.6.1.2.1.31.1.1.1.1"  # ifDescr
        )

        # Build MAC->port mapping
        mac_to_port: dict[str, dict[str, Any]] = {}
        for mac, port_idx in fdb_to_port.items():
            port_name = if_descr.get(port_idx, f"port-{port_idx}")
            mac_to_port[mac] = {"port_index": port_idx, "port_name": port_name}

        # LLDP-MIB: remote devices
        lldp_remotes = await self._snmp_walk(
            switch_ip, "1.0.8802.1.1.2.1.4.1.1"  # lldpRemTable
        )
        for chassis_oid, value in lldp_remotes.items():  # noqa: B007
            parts = chassis_oid.split(".")
            if len(parts) >= 8:
                chassis_id = ".".join(parts[7:])
                port_idx = parts[6] if len(parts) > 6 else "0"
                mac = self._oid_to_mac(chassis_oid)
                mac_to_port.setdefault(mac, {}).update({
                    "lldp_chassis_id": str(chassis_id),
                    "port_index": port_idx,
                })

        # CDP-MIB (Cisco): cdpCacheDeviceId, cdpCacheDevicePort
        cdp_devices = await self._snmp_walk(
            switch_ip, "1.3.6.1.4.1.9.9.23.1.2.1.1.6"  # cdpCacheDeviceId
        )
        for oid, value in cdp_devices.items():
            parts = oid.split(".")
            if len(parts) >= 7:
                if_index = parts[6]
                mac = self._oid_to_mac(oid)
                mac_to_port.setdefault(mac, {}).update({
                    "cdp_device_id": str(value),
                    "port_index": if_index,
                })

        # Convert to list
        for mac, info in mac_to_port.items():
            topology.append({
                "mac": mac,
                "port_name": info.get("port_name", info.get("port_index", "")),
                "lldp_chassis_id": info.get("lldp_chassis_id", ""),
                "cdp_device_id": info.get("cdp_device_id", ""),
            })

        return topology

    async def _snmp_walk(self, host: str, oid: str) -> dict[str, str]:
        """Perform an SNMPv2c walk and return {full_oid: value}."""
        results: dict[str, str] = {}
        try:
            from pysnmp.hlapi.asyncio import (
                CommandGenerator,
                CommunityData,
                ContextData,
                ObjectIdentity,
                ObjectType,
                UdpTransportTarget,
            )

            transport = UdpTransportTarget(
                (host, 161),
                timeout=self._snmp_timeout,
                retries=self._snmp_retries,
            )
            community = CommunityData(self._community, mpModel=1)  # SNMPv2c

            async def _walk() -> dict[str, str]:
                walk_results: dict[str, str] = {}
                for (
                    error_indication,
                    error_status,
                    error_index,  # noqa: B007
                    var_binds,
                ) in CommandGenerator().bulkCmd(
                    community,
                    transport,
                    ContextData(),
                    0,
                    25,
                    ObjectType(ObjectIdentity(oid)),
                    lexicographicMode=False,
                    lookupMib=False,
                ):
                    if error_indication or error_status:
                        break
                    for var_bind in var_binds:
                        name, val = var_bind
                        walk_results[str(name)] = str(val)
                return walk_results

            try:
                results = await asyncio.wait_for(_walk(), timeout=self._snmp_timeout + 5)
            except Exception as exc:
                logger.debug("SNMP walk failed for %s oid %s: %s", host, oid, exc)

        except ImportError:
            logger.debug("pysnmp not installed; install it to enable SNMP discovery")
        except Exception as exc:
            logger.debug("SNMP error for %s: %s", host, exc)

        return results

    # ------------------------------------------------------------------
    # Local interfaces
    # ------------------------------------------------------------------

    async def _collect_local_interfaces(self) -> list[dict[str, Any]]:
        """Collect local interface information."""
        try:
            ps_cmd = (
                "Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias * "
                "| Select-Object InterfaceAlias, IPAddress, PrefixLength "
                "| ConvertTo-Json -Depth 3"
            )
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-Command", ps_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            data = self._parse_json(stdout.decode())
            if isinstance(data, dict):
                data = [data]
            return [
                {
                    "name": i.get("InterfaceAlias", ""),
                    "ip": i.get("IPAddress", ""),
                    "prefix_length": i.get("PrefixLength", 0),
                }
                for i in data
            ]
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Merge / helpers
    # ------------------------------------------------------------------

    def _merge_arp_with_switch(
        self,
        devices: list[dict[str, Any]],
        switch_topology: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Join ARP devices with switch port data."""
        # Build lookup: MAC -> switch/port
        mac_lookup: dict[str, dict[str, Any]] = {}
        for st in switch_topology:
            switch_ip = st.get("switch_ip", "")
            for entry in st.get("topology", []):
                mac = entry.get("mac", "")
                if mac:
                    mac_lookup[mac] = {
                        "switch_ip": switch_ip,
                        "switch_port": entry.get("port_name", ""),
                        "lldp_chassis_id": entry.get("lldp_chassis_id", ""),
                        "cdp_device_id": entry.get("cdp_device_id", ""),
                    }

        merged: list[dict[str, Any]] = []
        for dev in devices:
            mac = dev.get("mac", "")
            merged.append({**dev, **mac_lookup.get(mac, {})})
        return merged

    @staticmethod
    def _normalize_mac(mac: str) -> str:
        mac = mac.strip().lower().replace("-", ":")
        if len(mac) == 12:
            return ":".join(mac[i : i + 2] for i in range(0, 12, 2))
        return mac

    @staticmethod
    def _oid_to_mac(oid: str) -> str:
        """Convert SNMP OID suffix to MAC address."""
        parts = oid.split(".")
        hex_bytes = parts[-6:]
        try:
            return ":".join(f"{int(b):02x}" for b in hex_bytes)
        except Exception:
            return oid

    @staticmethod
    def _parse_json(text: str) -> Any:
        import json

        try:
            return json.loads(text)
        except Exception:
            return None
