"""Mission Control Agent - Inventory collection."""

import logging
import os
import platform
import socket
import subprocess
import time
from typing import Any

import psutil

logger = logging.getLogger("mc-agent")


class InventoryCollector:
    """Collects system inventory data from the local machine."""

    def __init__(self) -> None:
        self._last_version = 0
        self._last_collected: dict[str, Any] = {}

    def collect(self) -> dict[str, Any]:
        """Gather comprehensive system inventory."""
        try:
            inventory = {
                "system": self._collect_system(),
                "cpu": self._collect_cpu(),
                "memory": self._collect_memory(),
                "disks": self._collect_disks(),
                "network": self._collect_network(),
                "services": self._collect_services(),
                "docker": self._collect_docker(),
                "software": self._collect_software(),
                "bios": self._collect_bios(),
                "tpm": self._collect_tpm(),
                "hardware": self._collect_hardware_info(),
                "virtualization": self._collect_virtualization(),
                "updates": self._collect_updates(),
            }
            self._last_version = int(time.time())
            self._last_collected = inventory
            return inventory
        except Exception as e:
            logger.error("Inventory collection failed: %s", e)
            return {"error": str(e)}

    def collect_incremental(self, last_version: int = 0) -> dict[str, Any]:
        """Only collect sections that changed since last_version."""
        if not self._last_collected or self._last_version <= last_version:
            return self.collect()

        changed: dict[str, Any] = {}
        collectors = {
            "system": self._collect_system,
            "cpu": self._collect_cpu,
            "memory": self._collect_memory,
            "disks": self._collect_disks,
            "network": self._collect_network,
            "services": self._collect_services,
            "docker": self._collect_docker,
            "software": self._collect_software,
            "bios": self._collect_bios,
            "tpm": self._collect_tpm,
            "hardware": self._collect_hardware_info,
            "virtualization": self._collect_virtualization,
            "updates": self._collect_updates,
        }

        for section, collector in collectors.items():
            try:
                new_data = collector()
                old_data = self._last_collected.get(section)
                if new_data != old_data:
                    changed[section] = new_data
            except Exception as e:
                logger.warning("Incremental collection of '%s' failed: %s", section, e)
                changed[section] = self._last_collected.get(section, {})

        self._last_version = int(time.time())
        for section, data in changed.items():
            self._last_collected[section] = data

        changed["inventory_version"] = self._last_version
        return changed

    def collect_health_metrics(self) -> dict[str, float]:
        """Collect current health metrics (CPU, memory, disk)."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent
                if platform.system() != "Windows"
                else psutil.disk_usage("C:\\").percent,
            }
        except Exception:
            return {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "disk_percent": 0.0,
            }

    def _collect_system(self) -> dict[str, Any]:
        """Collect basic system information."""
        boot = psutil.boot_time()
        uptime = psutil.time.time() - boot if boot else 0
        return {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor() or "unknown",
            "python_version": platform.python_version(),
            "uptime_seconds": int(uptime),
            "boot_time": boot,
        }

    def _collect_cpu(self) -> dict[str, Any]:
        """Collect CPU information."""
        return {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "percent": psutil.cpu_percent(interval=0.5),
            "freq": self._get_cpu_freq(),
            "load_average": self._get_load_average(),
        }

    def _get_cpu_freq(self) -> dict[str, Any] | None:
        try:
            freq = psutil.cpu_freq()
            if freq:
                return {
                    "current": freq.current,
                    "min": freq.min,
                    "max": freq.max,
                }
        except Exception:
            pass
        return None

    def _get_load_average(self) -> list[float] | None:
        try:
            if hasattr(os, "getloadavg"):
                return list(os.getloadavg())
        except Exception:
            pass
        return None

    def _collect_memory(self) -> dict[str, Any]:
        """Collect memory information."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent,
            "swap_total": swap.total,
            "swap_used": swap.used,
            "swap_percent": swap.percent,
        }

    def _collect_disks(self) -> list[dict[str, Any]]:
        """Collect disk information."""
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append(
                    {
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent,
                    }
                )
            except PermissionError:
                continue
        return disks

    def _collect_network(self) -> dict[str, Any]:
        """Collect network information."""
        interfaces = {}
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        io = psutil.net_io_counters()

        for name, addr_list in addrs.items():
            iface = {"addresses": [], "is_up": False}
            if name in stats:
                iface["is_up"] = stats[name].isup
                iface["speed"] = stats[name].speed
            for addr in addr_list:
                iface["addresses"].append(
                    {
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                    }
                )
            interfaces[name] = iface

        return {
            "interfaces": interfaces,
            "io": {
                "bytes_sent": io.bytes_sent,
                "bytes_recv": io.bytes_recv,
                "packets_sent": io.packets_sent,
                "packets_recv": io.packets_recv,
            }
            if io
            else {},
        }

    def _collect_services(self) -> list[dict[str, Any]]:
        """Collect running services/processes."""
        services = []
        try:
            for proc in psutil.process_iter(
                ["pid", "name", "status", "cpu_percent", "memory_percent"]
            ):
                info = proc.info
                if info["status"] == psutil.STATUS_RUNNING:
                    services.append(
                        {
                            "pid": info["pid"],
                            "name": info["name"],
                            "status": info["status"],
                            "cpu_percent": info.get("cpu_percent"),
                            "memory_percent": info.get("memory_percent"),
                        }
                    )
        except Exception as e:
            logger.warning("Service collection failed: %s", e)
        return services[:100]

    def _collect_docker(self) -> dict[str, Any]:
        """Collect Docker information if available."""
        try:
            import docker

            client = docker.from_env()
            info = client.info()
            containers = client.containers.list(all=True)
            return {
                "available": True,
                "version": info.get("ServerVersion", "unknown"),
                "container_count": len(containers),
                "containers": [
                    {
                        "id": c.short_id,
                        "name": c.name,
                        "status": c.status,
                        "image": str(c.image.tags)
                        if c.image.tags
                        else str(c.image.id)[:12],
                    }
                    for c in containers[:50]
                ],
            }
        except Exception:
            return {"available": False}

    def _collect_software(self) -> dict[str, Any]:
        """Collect installed software/packages."""
        system = platform.system()
        result = {"system": system, "packages": []}

        if system == "Linux":
            result["packages"] = self._get_linux_packages()
        elif system == "Windows":
            result["packages"] = self._get_windows_packages()
        elif system == "Darwin":
            result["packages"] = self._get_macos_packages()

        return result

    def _get_linux_packages(self) -> list[str]:
        """Get installed packages on Linux."""
        try:
            out = subprocess.check_output(
                ["dpkg", "--get-selections"],
                timeout=10,
                stderr=subprocess.DEVNULL,
            ).decode()
            return [
                line.split()[0]
                for line in out.strip().split("\n")
                if line.strip() and "install" in line
            ][:200]
        except Exception:
            pass

        try:
            out = subprocess.check_output(
                ["rpm", "-qa", "--queryformat", "%{NAME}\n"],
                timeout=10,
                stderr=subprocess.DEVNULL,
            ).decode()
            return out.strip().split("\n")[:200]
        except Exception:
            pass

        return []

    def _get_windows_packages(self) -> list[str]:
        """Get installed packages on Windows."""
        try:
            cmd = (
                "Get-ItemProperty"
                " HKLM:\\Software\\Microsoft\\Windows"
                "\\CurrentVersion\\Uninstall\\*"
                " | Select-Object -ExpandProperty DisplayName"
            )
            out = subprocess.check_output(
                [
                    "powershell",
                    "-Command",
                    cmd,
                ],
                timeout=30,
                stderr=subprocess.DEVNULL,
            ).decode()
            return [p.strip() for p in out.strip().split("\n") if p.strip()][:200]
        except Exception:
            return []

    def _get_macos_packages(self) -> list[str]:
        """Get installed packages on macOS."""
        try:
            out = subprocess.check_output(
                ["brew", "list", "--formula"],
                timeout=10,
                stderr=subprocess.DEVNULL,
            ).decode()
            return out.strip().split("\n")[:200]
        except Exception:
            return []

    def _collect_bios(self) -> dict[str, Any]:
        """Collect BIOS/UEFI information."""
        info: dict[str, Any] = {}
        system = platform.system()

        if system == "Linux":
            dmi = "/sys/class/dmi/id"
            for key, field in (
                ("vendor", "bios_vendor"),
                ("version", "bios_version"),
                ("date", "bios_date"),
            ):
                try:
                    path = os.path.join(dmi, field)
                    if os.path.exists(path):
                        with open(path) as f:
                            info[key] = f.read().strip()
                except Exception:
                    pass

        elif system == "Windows":
            try:
                out = subprocess.check_output(
                    [
                        "wmic",
                        "bios",
                        "get",
                        "Manufacturer,SMBIOSBIOSVersion,ReleaseDate",
                    ],
                    timeout=10,
                    stderr=subprocess.DEVNULL,
                ).decode(errors="replace")
                lines = [
                    length.strip()
                    for length in out.strip().split("\n")
                    if length.strip()
                    and length.strip().upper()
                    not in ("MANUFACTURER", "SMBIOSBIOSVERSION", "RELEASEDATE")
                ]
                if len(lines) >= 3:
                    info["vendor"] = lines[0]
                    info["version"] = lines[1]
                    info["date"] = lines[2]
            except Exception:
                pass

        elif system == "Darwin":
            try:
                out = subprocess.check_output(
                    ["system_profiler", "SPHardwareDataType"],
                    timeout=10,
                    stderr=subprocess.DEVNULL,
                ).decode()
                for line in out.strip().split("\n"):
                    if "ROM" in line and ":" in line:
                        info["version"] = line.split(":", 1)[-1].strip()
            except Exception:
                pass

        return info

    def _collect_tpm(self) -> dict[str, Any]:
        """Collect TPM status."""
        info: dict[str, Any] = {"available": False}
        system = platform.system()

        if system == "Linux":
            try:
                subprocess.check_output(
                    ["tpm2_getcap", "properties-fixed"],
                    timeout=5,
                    stderr=subprocess.DEVNULL,
                )
                info["available"] = True
                try:
                    with open("/sys/class/tpm/tpm0/device") as f:
                        info["device"] = f.read().strip()
                except Exception:
                    pass
            except Exception:
                try:
                    if os.path.exists("/dev/tpm0"):
                        info["available"] = True
                except Exception:
                    pass

        elif system == "Windows":
            try:
                out = subprocess.check_output(
                    [
                        "powershell",
                        "-Command",
                        "Get-Tpm | Select-Object -Property TpmPresent,TpmEnabled,TpmReady",
                    ],
                    timeout=10,
                    stderr=subprocess.DEVNULL,
                ).decode()
                info["available"] = "True" in out
                for line in out.strip().split("\n"):
                    line = line.strip()
                    if "True" in line or "False" in line:
                        parts = [
                            p.strip()
                            for p in line.split()
                            if p.strip() in ("True", "False")
                        ]
                        if len(parts) >= 3:
                            info["present"] = parts[0] == "True"
                            info["enabled"] = parts[1] == "True"
                            info["ready"] = parts[2] == "True"
                            break
            except Exception:
                pass

        return info

    def _collect_hardware_info(self) -> dict[str, Any]:
        """Collect motherboard, manufacturer, model, serial."""
        info: dict[str, Any] = {}
        system = platform.system()

        if system == "Linux":
            dmi = "/sys/class/dmi/id"
            for key, field in (
                ("manufacturer", "board_vendor"),
                ("model", "board_name"),
                ("serial", "board_serial"),
                ("system_manufacturer", "sys_vendor"),
                ("system_model", "product_name"),
                ("system_serial", "product_serial"),
            ):
                try:
                    path = os.path.join(dmi, field)
                    if os.path.exists(path):
                        with open(path) as f:
                            info[key] = f.read().strip()
                except Exception:
                    pass

        elif system == "Windows":
            try:
                out = subprocess.check_output(
                    ["wmic", "baseboard", "get", "Manufacturer,Product,SerialNumber"],
                    timeout=10,
                    stderr=subprocess.DEVNULL,
                ).decode(errors="replace")
                lines = [
                    length.strip()
                    for length in out.strip().split("\n")
                    if length.strip()
                    and length.strip().upper()
                    not in ("MANUFACTURER", "PRODUCT", "SERIALNUMBER")
                ]
                if len(lines) >= 3:
                    info["manufacturer"] = lines[0]
                    info["model"] = lines[1]
                    info["serial"] = lines[2]
            except Exception:
                pass

        elif system == "Darwin":
            try:
                out = subprocess.check_output(
                    ["system_profiler", "SPHardwareDataType"],
                    timeout=10,
                    stderr=subprocess.DEVNULL,
                ).decode()
                for line in out.strip().split("\n"):
                    if ":" in line:
                        key, _, val = line.partition(":")
                        key = key.strip().lower().replace(" ", "_")
                        val = val.strip()
                        if key in (
                            "model_name",
                            "model_identifier",
                            "manufacturer",
                            "serial_number",
                        ):
                            info[key] = val
            except Exception:
                pass

        return info

    def _collect_virtualization(self) -> dict[str, Any]:
        """Detect hypervisor environment."""
        info: dict[str, Any] = {
            "is_virtual": False,
            "hypervisor": None,
            "cloud_provider": None,
        }
        system = platform.system()

        try:
            vendor_path = "/sys/class/dmi/id/sys_vendor"
            board_path = "/sys/class/dmi/id/board_name"
            chassis_path = "/sys/class/dmi/id/chassis_asset_tag"

            vendor = ""
            board = ""
            chassis = ""

            if system == "Linux":
                for attr, path in (
                    ("vendor", vendor_path),
                    ("board", board_path),
                    ("chassis", chassis_path),
                ):
                    try:
                        if os.path.exists(path):
                            with open(path) as f:
                                if attr == "vendor":
                                    vendor = f.read().strip().lower()
                                elif attr == "board":
                                    board = f.read().strip().lower()
                                else:
                                    chassis = f.read().strip().lower()
                    except Exception:
                        pass

            hypervisor_map = {
                "vmware": "VMware",
                "virtualbox": "VirtualBox",
                "kvm": "KVM",
                "qemu": "KVM",
                "microsoft corporation": "Hyper-V",
                "xen": "Xen",
                "parallels": "Parallels",
                "proxmox": "Proxmox",
                "oracle": "VirtualBox",
            }

            for pattern, name in hypervisor_map.items():
                if pattern in vendor or pattern in board or pattern in chassis:
                    info["hypervisor"] = name
                    info["is_virtual"] = True
                    break

            if "hv" in vendor or "hyper-v" in board:
                info["hypervisor"] = "Hyper-V"
                info["is_virtual"] = True

        except Exception as e:
            logger.debug("Virtualization detection failed: %s", e)

        if not info["is_virtual"]:
            cloud_checks = [
                ("/sys/class/dmi/id/sys_vendor", "amazon ec2", "AWS"),
                ("/sys/class/dmi/id/sys_vendor", "google compute engine", "GCP"),
                ("/sys/class/dmi/id/sys_vendor", "microsoft corporation", "Azure"),
                ("/sys/class/dmi/id/chassis_asset_tag", "amazon ec2", "AWS"),
                ("/run/cloud-init/instance-data.json", None, None),
                ("/var/lib/cloud/data/instance-id", None, None),
            ]
            for path, match_str, provider in cloud_checks:  # noqa: B007
                try:
                    if not os.path.exists(path):
                        continue
                    if path.endswith(".json"):
                        import json

                        with open(path) as f:
                            data = json.load(f)
                        ds = data.get("ds", {}).get("meta_data", {})
                        if ds.get("cloud-provider") or ds.get("platform") == "ec2":
                            info["is_virtual"] = True
                            info["cloud_provider"] = ds.get("cloud-provider", "AWS")
                            break
                    else:
                        with open(path) as f:
                            content = f.read().strip().lower()
                        if "amazon" in content or "ec2" in content:
                            info["is_virtual"] = True
                            info["cloud_provider"] = "AWS"
                            break
                        elif "google" in content:
                            info["is_virtual"] = True
                            info["cloud_provider"] = "GCP"
                            break
                        elif "microsoft" in content and provider:
                            info["is_virtual"] = True
                            info["cloud_provider"] = "Azure"
                            break
                except Exception:
                    continue

        return info

    def _collect_updates(self) -> dict[str, Any]:
        """Collect pending OS updates count."""
        info: dict[str, Any] = {"pending_count": 0, "available": False}
        system = platform.system()

        if system == "Linux":
            try:
                subprocess.check_output(
                    ["apt-get", "-s", "upgrade"],
                    timeout=15,
                    stderr=subprocess.DEVNULL,
                )
                info["available"] = True
                try:
                    out = subprocess.check_output(
                        ["apt-cache", "unattended-upgrade", "--list"],
                        timeout=10,
                        stderr=subprocess.DEVNULL,
                    ).decode()
                    info["pending_count"] = len(
                        [length for length in out.strip().split("\n") if length.strip()]
                    )
                except Exception:
                    pass
            except Exception:
                try:
                    out = subprocess.check_output(
                        ["yum", "check-update", "--quiet"],
                        timeout=30,
                        stderr=subprocess.DEVNULL,
                    ).decode()
                    info["pending_count"] = len(
                        [length for length in out.strip().split("\n") if length.strip()]
                    )
                    info["available"] = info["pending_count"] > 0
                except subprocess.CalledProcessError as e:
                    if e.output:
                        lines = [
                            length
                            for length in e.output.decode().strip().split("\n")
                            if length.strip()
                        ]
                        info["pending_count"] = max(0, len(lines) - 1)
                        info["available"] = info["pending_count"] > 0
                except Exception:
                    pass

        elif system == "Windows":
            try:
                out = (
                    subprocess.check_output(
                        [
                            "powershell",
                            "-Command",
                            "(New-Object -ComObject Microsoft.Update.Session).CreateUpdateSearcher().Search('IsInstalled=0').Updates.Count",
                        ],
                        timeout=30,
                        stderr=subprocess.DEVNULL,
                    )
                    .decode()
                    .strip()
                )
                info["pending_count"] = int(out) if out.isdigit() else 0
                info["available"] = info["pending_count"] > 0
            except Exception:
                pass

        return info
