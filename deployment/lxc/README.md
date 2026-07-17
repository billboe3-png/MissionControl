# Mission Control — Proxmox LXC Deployment

Deploy Mission Control as an Ubuntu LXC container on Proxmox VE.

## Quick Start

```bash
# 1. Create Ubuntu 24.04 LXC on Proxmox
# 2. Enable nesting + keyctl
pct set <VMID> -features nesting=1,keyctl=1

# 3. Enter the container
pct enter <VMID>

# 4. Install Mission Control
curl -sL https://raw.githubusercontent.com/mission-control/mission-control/main/deployment/lxc/scripts/install.sh | sudo bash
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/INSTALL.md](docs/INSTALL.md) | Installation guide |
| [docs/UPGRADE.md](docs/UPGRADE.md) | Upgrade instructions |
| [docs/BACKUP.md](docs/BACKUP.md) | Backup procedures |
| [docs/RESTORE.md](docs/RESTORE.md) | Restore procedures |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues and fixes |
| [docs/LXC-REQUIREMENTS.md](docs/LXC-REQUIREMENTS.md) | LXC container requirements |
| [docs/DIRECTORY-LAYOUT.md](docs/DIRECTORY-LAYOUT.md) | File system layout |

## Directory Structure

```
deployment/lxc/
├── scripts/
│   ├── install.sh          # Main installer (idempotent)
│   ├── update.sh           # Upgrade with backup + rollback
│   ├── backup.sh           # Timestamped backups
│   ├── restore.sh          # Restore from backup
│   ├── health.sh           # Comprehensive health check
│   ├── firstboot.sh        # First-boot setup
│   └── clean-template.sh   # Prepare for Proxmox template
├── docker/
│   └── docker-compose.yml  # LXC-optimized compose file
├── docs/
│   ├── INSTALL.md
│   ├── UPGRADE.md
│   ├── BACKUP.md
│   ├── RESTORE.md
│   ├── TROUBLESHOOTING.md
│   ├── LXC-REQUIREMENTS.md
│   └── DIRECTORY-LAYOUT.md
├── templates/
│   └── (Proxmox template configs)
└── config/
    └── (Default configuration files)
```

## Management Commands

After installation, these commands are available system-wide:

| Command | Description |
|---------|-------------|
| `mc-status` | Show container status |
| `mc-health` | Run health checks |
| `mc-logs` | View service logs |
| `mc-restart` | Restart services |
| `mc-update` | Update Mission Control |
| `mc-backup` | Create backup |
| `mc-restore` | Restore from backup |

## Requirements

- Proxmox VE 7.0+
- Ubuntu 24.04 LXC container
- 4 vCPU, 8 GB RAM, 80 GB storage
- Nesting and keyctl enabled
- Internet access

See [docs/LXC-REQUIREMENTS.md](docs/LXC-REQUIREMENTS.md) for full requirements.

## License

MIT
