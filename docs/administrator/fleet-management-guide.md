# Fleet Management Guide

> Sprint 3.9.1 — Operations Workspace & Fleet Dashboard

## Overview

Mission Control provides a comprehensive Fleet Management interface for monitoring and managing all agents across your infrastructure.

## Operations Dashboard

The Operations Dashboard (`/`) is the primary interface, providing a single-pane-of-glass view with auto-refreshing widgets:

- **Fleet Widget** — Total, online, and offline agent counts with health bar
- **Infrastructure Widget** — Companies, sites, plugins, and integrations
- **System Widget** — PostgreSQL, Redis, Event Bus, Heartbeat, Scheduler, Automation, Plugin Loader, Fleet State, AI Service health with latency
- **System Overview Widget** — Backend, Docker, Git status
- **Automation Widget** — Playbooks, running, completed, failed, pending approvals
- **AI Engine Widget** — Health score, incidents, recommendations, correlated alerts, top risks
- **Activity Widget** — Recent commands with status
- **Companies & Sites Widget** — Company and site counts
- **AI Insights Widget** — Automated infrastructure insights

All widgets refresh every 15 seconds automatically.

## Fleet Management Page

Accessed via `/fleet`, the Fleet Management page provides:

### Agent Table Features
- **Search** — Filter by name, hostname, OS, or IP
- **Multi-column sorting** — Click column headers to sort ascending/descending
- **Status filtering** — Filter by online/offline status
- **Bulk selection** — Select multiple agents via checkboxes

### Agent Columns
| Column | Description |
|--------|-------------|
| Agent | Name with status badge |
| Hostname | System hostname |
| OS | Operating system |
| Version | Agent version |
| Status | Online/Offline |
| Health | Healthy/Warning/Critical |
| CPU | CPU utilization bar |
| Memory | Memory utilization bar |
| Disk | Disk utilization bar |
| Last Heartbeat | Time since last heartbeat |
| Plugins | Active plugin count |

### Stats Bar
The top of the page shows aggregate fleet statistics:
- Total agents
- Online agents
- Offline agents
- Average CPU across fleet
- Average memory across fleet

## Agent Detail Workspace

Clicking an agent opens the detailed workspace at `/agents/:id` with tabs:

### Overview Tab
Agent identity, status, health, hostname, IP, OS, version, heartbeat, registration, tags, plugins.

### Performance Tab
Resource utilization (CPU, Memory, Disk) with visual health bars. Hardware information from inventory.

### Commands Tab
- **Status filters** — pending, running, completed, failed
- **Output viewer** — Expand command output inline
- **Execute form** — Send new commands to the agent

### Inventory Tab
Full inventory data as formatted JSON.

### Diagnostics Tab
Agent connectivity, heartbeat status, health score, enabled status.

### Configuration Tab
Heartbeat interval, enabled state, tags, notes.

### History Tab
Timeline of state changes and command history.

## Operations Timeline

Accessed via `/fleet/timeline`:

- **Live event stream** across all infrastructure
- **Search** — Filter events by message or source
- **Type filtering** — Filter by event type
- **Time range** — 1h, 6h, 24h, 7d, all time
- **Export CSV** — Download filtered events as CSV

## Command Center

Accessed via `/fleet/commands`:

- **Centralized command view** — All commands across all agents
- **Status filters** — pending, running, completed, failed, cancelled
- **Output viewer** — Expand command output inline
- **Retry** — Resubmit failed commands
- **Auto-refresh** — Updates every 10 seconds

## Health Center

Accessed via `/fleet/health`:

- **Subsystem health** — PostgreSQL, Redis, Event Bus, Dashboard Aggregator, Scheduler, Automation Engine, Plugin Loader, Heartbeat Service, Fleet State Engine, AI Service, Disk Space
- **Latency metrics** — Response time per subsystem
- **Status badges** — OK, Warning, Error per component
- **Auto-refresh** — Updates every 15 seconds

## Plugin Center

Accessed via `/fleet/plugins`:

- **Plugin listing** — All installed plugins
- **Status filtering** — Enabled/Disabled
- **Plugin details** — Name, version, SDK version, health, dependencies
- **Actions** — Enable, Disable, Restart, Configure, View Logs

## Company & Site Workspace

Accessed via `/fleet/companies`:

- **Company cards** — Display name, status, license, contact
- **Hierarchy view** — Company → Sites → Agents
- **Stats** — Site count, agent count, integration count per company
- **Auto-refresh** — Updates every 30 seconds

## Personal Dashboard

Accessed via `/settings/dashboard`:

- **Widget customization** — Toggle widget visibility
- **Widget reordering** — Move widgets up/down
- **Reset to defaults** — Restore default layout
- **Persistent preferences** — Saved to localStorage per browser

## Auto-Refresh Intervals

| Page | Interval |
|------|----------|
| Operations Dashboard | 15 seconds |
| Fleet Management | 15 seconds |
| Operations Timeline | 30 seconds |
| Command Center | 10 seconds |
| Health Center | 15 seconds |
| Company Workspace | 30 seconds |

## Architecture

All frontend pages communicate only with the DashboardService aggregation layer. No direct frontend communication with agents, plugins, databases, or infrastructure providers.

## API Endpoints Used

| Endpoint | Used By |
|----------|---------|
| `GET /api/v1/dashboard` | Operations Dashboard |
| `GET /api/v1/health/subsystems` | System Widget, Health Center |
| `GET /api/v1/agents` | Fleet Management, Fleet Widget |
| `GET /api/v1/agents/:id` | Agent Detail |
| `GET /api/v1/agents/:id/commands` | Agent Detail |
| `GET /api/v1/agents/:id/inventory` | Agent Detail |
| `GET /api/v1/agents/commands/all` | Command Center, Timeline, Activity Widget |
| `POST /api/v1/agents/:id/execute` | Agent Detail, Command Center |
| `GET /api/v1/companies` | Company Workspace |
