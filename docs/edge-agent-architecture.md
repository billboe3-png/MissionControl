# Mission Control Edge Agent Architecture

## Overview
The edge agent is a local collector that runs on-site, executes plugins where access already exists, persists data in local SQLite, and synchronizes with the cloud GCE backend when online. The cloud never connects into the LAN; all connectivity is outbound from edge to cloud.

## Core Principles
- **Edge-first execution**: plugins run on the local box
- **Local persistence**: SQLite survives cloud/network outages
- **Pull-based config**: the edge fetches config; nothing is pushed to offline agents
- **Versioned manifests**: cloud and edge agree on config/plugin schema versions
- **Delta sync**: only changed/new data moves over the wire

## Components
- `edge_core/` - main daemon/service
- `storage/` - SQLite repo + migrations
- `plugins/` - local plugin runtime
- `sync/` - config pull + data push
- `crypto/` - encrypted credential storage at rest
- `install/` - OS-specific packaging

## Data Flow
1. Edge boots, opens local SQLite
2. Edge pulls `/api/v1/edge/{agent_id}/config`
3. Core applies config only if `config_version` matches manifest or edge is offline-safe
4. Plugins run on schedule, write to local SQLite
5. Edge pushes new rows to `/api/v1/edge/{agent_id}/data`
6. Cloud updates dashboard/config from uploaded data

## Offline Behavior
- Edge continues collecting with last-known config
- Cloud marks agent `stale` after threshold
- When edge reconnects, it pulls newest config and resumes push
- No config is ever pushed to an offline edge

## Plugin Strategy
- Built-in plugins shipped with edge package
- New plugins fetched from cloud only when `manifest.plugins` changes
- Plugin files are checksum-verified before activation
- Rollback = keep previous plugin folder until new one passes health check

## Watch-outs
- SQLite uses WAL mode + single writer per process
- Credentials encrypted with per-agent key derived from install token + device secret
- Data pushes are compressed + chunked to avoid spikes
- Plugin schema version is explicit in manifest; cloud rejects incompatible data

## OS Support
- Linux: systemd unit + tarball/DEB
- Windows: existing bat installer + scheduled task
