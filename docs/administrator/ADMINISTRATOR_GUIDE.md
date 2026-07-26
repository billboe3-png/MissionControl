# Mission Control Administrator Guide

**Version:** 3.0.0
**Last Updated:** July 2026

---

## About Mission Control

Mission Control is a centralized infrastructure management platform built with FastAPI, SQLAlchemy 2.0, PostgreSQL 16, Redis 7, and React/TypeScript/Vite. It provides real-time monitoring, configuration management, and remote execution capabilities across distributed agent networks.

Mission Control is available in two editions:

- **Community** (`EDITION=community`) — Open-source edition with core functionality.
- **Enterprise** (`EDITION=enterprise`) — Extended edition with advanced RBAC, audit logging, and plugin marketplace access.

## Who This Guide Is For

This guide is for system administrators, DevOps engineers, and IT operations staff responsible for deploying, configuring, maintaining, and troubleshooting Mission Control installations.

## How to Use This Guide

Start with [Installation](INSTALLATION.md) if you are setting up a new instance. For existing installations, use the relevant sections for your needs. Cross-references are provided throughout each document.

---

## Table of Contents

| Document | Description |
|---|---|
| [Installation](INSTALLATION.md) | System requirements and deployment methods |
| [Configuration](CONFIGURATION.md) | All 42 environment variables and settings |
| [User Management](USER_MANAGEMENT.md) | User accounts, roles, and RBAC |
| [Company and Site Management](COMPANY_AND_SITE_MANAGEMENT.md) | Multi-tenant hierarchy and data isolation |
| [Agent Deployment](AGENT_DEPLOYMENT.md) | Agent installation, registration, and maintenance |
| [Plugin Management](PLUGIN_MANAGEMENT.md) | Plugin lifecycle and marketplace |
| [Backup and Restore](BACKUP_AND_RESTORE.md) | Data protection and disaster recovery |
| [Upgrades](UPGRADES.md) | Version upgrade and rollback procedures |
| [Troubleshooting](TROUBLESHOOTING.md) | Common issues and diagnostic procedures |
| [Monitoring](MONITORING.md) | Health endpoints and system observability |
| [Logging](LOGGING.md) | Log management and structured logging |
| [Performance](PERFORMANCE.md) | Tuning and production sizing |
| [Security Hardening](SECURITY_HARDENING.md) | TLS, firewalls, and security best practices |
| [FAQ](FAQ.md) | Frequently asked questions |

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  Dashboard (React)               │
│                  Port 3000                       │
└──────────────────────┬──────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────┐
│              API Gateway (FastAPI)                │
│              Port 8000, 25 routers               │
│              286 endpoints, JWT auth              │
└─────┬────────────┬────────────┬─────────────────┘
      │            │            │
┌─────▼─────┐ ┌────▼─────┐ ┌───▼────────────────┐
│PostgreSQL 16│ │Redis 7   │ │  Plugin System     │
│ 29 tables  │ │Cache/Queue│ │ server/agent/hybrid│
│ Alembic    │ │Event Bus  │ │ Marketplace        │
└────────────┘ └──────────┘ └────────────────────┘
      │
┌─────▼──────────────────────────────────────────┐
│              Agent Network                      │
│  Python 3.12, config at ~/.config/mission-     │
│  control-agent/config.yaml                     │
│  Heartbeat, API key auth, offline mode          │
└────────────────────────────────────────────────┘
```

## Key Concepts

- **Companies** represent organizational tenants. Each company's data is isolated.
- **Sites** represent physical or logical locations within a company.
- **Agents** are lightweight Python daemons running on managed hosts.
- **Plugins** extend functionality — server plugins run in the API process, agent plugins run on remote hosts, hybrid plugins span both.
- **Events** flow through a Redis-backed event bus for real-time updates.
