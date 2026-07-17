# Mission Control — Standard Directory Layout

## Installation Path

All Mission Control files are installed under `/opt/missioncontrol`:

```
/opt/missioncontrol/
├── docker-compose.yml          # Docker Compose configuration
├── .env                        # Environment variables (secrets, database config)
├── .env.example                # Template for .env
├── nginx/                      # Nginx reverse proxy configuration
│   └── default.conf
├── config/                     # Application configuration
│   └── plugins/                # Plugin configuration files
├── data/                       # Persistent data
│   ├── postgres/               # PostgreSQL data (via Docker volume)
│   └── redis/                  # Redis data (via Docker volume)
├── backups/                    # Backup storage
│   ├── db/                     # Database backups
│   ├── config/                 # Configuration backups
│   └── full/                   # Full system backups
├── logs/                       # Application logs
│   ├── nginx/                  # Nginx access/error logs
│   └── backup/                 # Backup operation logs
├── plugins/                    # Installed plugins
├── playbooks/                  # Ansible playbooks
├── automation/                 # Automation scripts and configs
└── scripts/                    # Management scripts
    ├── install.sh              # Installer
    ├── update.sh               # Updater
    ├── backup.sh               # Backup script
    ├── restore.sh              # Restore script
    ├── health.sh               # Health check
    ├── firstboot.sh            # First boot setup
    └── clean-template.sh       # Template preparation
```

## Docker Volumes

Persistent data is stored in named Docker volumes:

| Volume | Host Path | Container Path | Purpose |
|--------|-----------|----------------|---------|
| `postgres_data` | Docker managed | `/var/lib/postgresql/data` | PostgreSQL database |
| `redis_data` | Docker managed | `/data` | Redis persistence |

## Bind Mounts

Configuration and logs use bind mounts for easy host access:

| Host Path | Container Path | Mode | Purpose |
|-----------|----------------|------|---------|
| `/opt/missioncontrol/nginx/` | `/etc/nginx/conf.d/` | ro | Nginx config |
| `/opt/missioncontrol/logs/nginx/` | `/var/log/nginx/` | rw | Nginx logs |
| `/opt/missioncontrol/config/` | `/app/config/` | rw | Plugin config |

## Backup Locations

Backups are stored with timestamps:

```
/opt/missioncontrol/backups/
├── db/
│   └── missioncontrol_20260717_143022.sql.gz
├── config/
│   └── missioncontrol_config_20260717_143022.tar.gz
└── full/
    └── missioncontrol_full_20260717_143022.tar.gz
```

## Log Rotation

- Docker container logs: 10MB max, 3 files rotation
- Nginx logs: managed by logrotate
- Application logs: rotated by backup script before cleanup

## Disk Space Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS + Docker | 5 GB | 10 GB |
| PostgreSQL data | 10 GB | 20 GB |
| Backups | 10 GB | 20 GB |
| Logs | 2 GB | 5 GB |
| **Total** | **27 GB** | **55 GB** |

The LXC container should be allocated at least 80 GB to accommodate growth.
