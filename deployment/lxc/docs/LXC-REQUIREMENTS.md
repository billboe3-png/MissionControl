# Mission Control — LXC Requirements

## Minimum Hardware Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| vCPU | 4 | 4 |
| RAM | 8 GB | 8 GB |
| Storage | 80 GB | 120 GB |
| Swap | 0 | 0 (Docker manages memory) |

## Operating System

- **Required:** Ubuntu 24.04 LTS (Noble Numbat)
- **Alternative:** Debian 12 (Bookworm)
- **Architecture:** amd64 only

## Proxmox LXC Settings

### Container Type

- **Unprivileged container** (preferred for security)
- Rootless mode supported but not required

### Required Features

These Proxmox features MUST be enabled for Docker to work inside the LXC:

| Feature | Setting | How to Enable |
|---------|---------|---------------|
| Nesting | `features: nesting=1` | `pct set <VMID> -features nesting=1` |
| Keyctl | `features: keyctl=1` | `pct set <VMID> -features keyctl=1` |

Without these, Docker will fail to start containers inside the LXC.

### Network Configuration

- **Bridge:** `vmbr0` (default Proxmox bridge)
- **DHCP:** Supported (default)
- **Static IP:** Supported and recommended for production
- **Firewall:** Optional, but recommended

Example static IP configuration:
```
net0: name=eth0,bridge=vmbr0,hwaddr=auto,ip=192.168.1.100/24,gw=192.168.1.1
```

### Storage

- **Root disk:** Minimum 80 GB
- **Storage type:** Any Proxmox-supported storage (local-lvm, zfs, ceph)
- **Filesystem:** ext4 (default) or xfs

### Security Settings

| Setting | Value | Reason |
|---------|-------|--------|
| `features:nesting` | 1 | Required for Docker-in-LXC |
| `features:keyctl` | 1 | Required for Docker secrets |
| `unprivileged` | 1 | Security best practice |
| `password` | Set during creation | Root access |

## Systemd Requirements

Docker requires systemd to function. The LXC must have:

- systemd as PID 1 (default for Ubuntu/Debian LXC)
- Docker service enabled at boot
- Network-online.target properly configured

## Docker Requirements

- Docker Engine CE (latest stable)
- Docker Compose plugin v2+
- Docker CLI accessible as root

## Network Requirements

| Port | Protocol | Purpose |
|------|----------|---------|
| 80 | TCP | HTTP (nginx) |
| 443 | TCP | HTTPS (optional, for TLS termination) |
| 22 | TCP | SSH (management access) |

## Proxmox Host Requirements

- Proxmox VE 7.0+ (tested on 9.2)
- Internet access for Docker image pulls
- DNS resolution working inside LXC

## Verification Commands

After creating the LXC, verify it's ready:

```bash
# Enter the container
pct enter <VMID>

# Check nesting is working
cat /proc/self/status | grep -i nesting

# Check Docker can start
systemctl start docker
docker info

# Check keyctl support
keyctl session true
```

## Common Issues

### Docker fails to start

**Symptom:** `Cannot connect to the Docker daemon`

**Fix:** Enable nesting and keyctl:
```bash
pct set <VMID> -features nesting=1,keyctl=1
pct restart <VMID>
```

### Cannot create containers inside LXC

**Symptom:** `error creating overlay mount...`

**Fix:** Ensure the LXC storage supports user namespaces. For ZFS, enable the `zfs` feature in Proxmox storage config.

### Network unreachable after boot

**Symptom:** No IP address assigned

**Fix:** Check `/etc/network/interfaces` and ensure DHCP is configured, or set a static IP.
