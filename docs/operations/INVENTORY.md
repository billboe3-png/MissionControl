# Inventory Management Guide

**Purpose:** Understanding and using inventory data collected by agents  
**Related:** [AGENTS.md](./AGENTS.md), [DASHBOARD.md](./DASHBOARD.md), [REPORTING.md](./REPORTING.md)

---

## Inventory Overview

Mission Control agents automatically collect inventory data from each managed host. Inventory is gathered during each heartbeat cycle (every 30 seconds) and transmitted as deltas — only changes since the last heartbeat are sent, reducing bandwidth and processing overhead.

Inventory is organized into four categories:
1. **System Inventory** — Hardware and OS details
2. **Software Inventory** — Installed packages and applications
3. **Service Inventory** — Running and configured services
4. **Network Inventory** — Interfaces, addresses, and configuration

---

## System Inventory

System inventory captures the fundamental characteristics of each host.

### Data Points

| Field | Type | Description |
|-------|------|-------------|
| `hostname` | string | System hostname |
| `domain` | string | Domain or workgroup |
| `osType` | string | Operating system type (`windows`, `linux`, `other`) |
| `osName` | string | Full OS name (e.g., `Ubuntu 22.04 LTS`) |
| `osVersion` | string | OS version string |
| `kernelVersion` | string | Kernel version (Linux) or build number (Windows) |
| `architecture` | string | System architecture (`x86_64`, `arm64`, etc.) |
| `cpuModel` | string | CPU model name |
| `cpuCores` | integer | Total CPU cores |
| `cpuThreads` | integer | Total CPU threads |
| `totalMemory` | string | Total physical memory (e.g., `64 GB`) |
| `systemUUID` | string | System UUID for hardware identification |
| `serialNumber` | string | Hardware serial number |
| `manufacturer` | string | Hardware manufacturer |
| `model` | string | Hardware model |

### Viewing System Inventory

**API Endpoint:** `GET /api/v1/agents/{agentId}/inventory/system`

**Via Dashboard:**
1. Navigate to the agent detail view.
2. Select the "Inventory" tab.
3. The "System" section displays all hardware and OS details.

---

## Software Inventory

Software inventory tracks all installed packages and applications on each host.

### Data Points

| Field | Type | Description |
|-------|------|-------------|
| `packages` | array | List of installed packages |
| `applications` | array | Detected applications |
| `pendingUpdates` | array | Available updates |
| `lastScanTime` | ISO 8601 timestamp | When software inventory was last collected |

### Package Entry

Each package in the `packages` array contains:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Package name |
| `version` | string | Installed version |
| `source` | string | Package repository or source |
| `installDate` | string | Date of installation |
| `size` | string | Installed size |

### Application Entry

Each application in the `applications` array contains:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Application name |
| `version` | string | Version string |
| `vendor` | string | Software vendor |
| `installPath` | string | Installation path |
| `licenseType` | string | License type if detectable |

### Viewing Software Inventory

**API Endpoint:** `GET /api/v1/agents/{agentId}/inventory/software`

**Via Dashboard:**
1. Navigate to the agent detail view.
2. Select the "Inventory" tab.
3. The "Software" section lists all installed packages and applications.
4. Use the search/filter controls to find specific packages.

---

## Service Inventory

Service inventory tracks system services, daemons, and background processes.

### Data Points

| Field | Type | Description |
|-------|------|-------------|
| `services` | array | List of services |
| `lastScanTime` | ISO 8601 timestamp | When service inventory was last collected |

### Service Entry

Each service contains:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Service name |
| `displayName` | string | Human-readable display name |
| `status` | string | `running`, `stopped`, `disabled`, `unknown` |
| `startType` | string | `automatic`, `manual`, `disabled` |
| `pid` | integer | Process ID (if running) |
| `user` | string | Account running the service |
| `description` | string | Service description |
| `dependencies` | array | Services that depend on this service |

### Viewing Service Inventory

**API Endpoint:** `GET /api/v1/agents/{agentId}/inventory/services`

**Via Dashboard:**
1. Navigate to the agent detail view.
2. Select the "Inventory" tab.
3. The "Services" section shows all detected services.
4. Filter by status to find stopped or disabled services.

---

## Network Inventory

Network inventory captures all network configuration on each host.

### Data Points

| Field | Type | Description |
|-------|------|-------------|
| `interfaces` | array | Network interfaces |
| `dnsServers` | array | Configured DNS servers |
| `dnsSuffix` | string | DNS search suffix |
| `defaultGateway` | string | Default gateway address |
| `hostname` | string | Network-reported hostname |
| `domain` | string | Network domain |

### Interface Entry

Each interface contains:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Interface name (e.g., `eth0`, `Ethernet`) |
| `macAddress` | string | MAC address |
| `ipAddresses` | array | Assigned IP addresses with subnet masks |
| `status` | string | `up`, `down`, `unknown` |
| `speed` | string | Link speed (e.g., `1 Gbps`) |
| `type` | string | `ethernet`, `wireless`, `loopback`, `virtual` |
| `dnsServers` | array | Interface-specific DNS servers |
| `dhcpEnabled` | boolean | Whether DHCP is enabled |

### Viewing Network Inventory

**API Endpoint:** `GET /api/v1/agents/{agentId}/inventory/network`

**Via Dashboard:**
1. Navigate to the agent detail view.
2. Select the "Inventory" tab.
3. The "Network" section shows all interfaces and their configuration.

---

## How Inventory Is Collected

Inventory collection is integrated into the agent heartbeat mechanism.

### Collection Process

1. **Heartbeat trigger:** Every 30 seconds, the agent initiates a heartbeat to the Mission Control server.
2. **Delta detection:** The agent compares current inventory state against the last reported state.
3. **Delta transmission:** Only changes (additions, modifications, removals) are transmitted in the heartbeat payload.
4. **Server processing:** Mission Control receives the delta and updates its inventory database.
5. **Acknowledgment:** The server confirms receipt in the heartbeat response.

### Collection Frequency

| Inventory Type | Collection Method | Frequency |
|----------------|-------------------|-----------|
| System | Full scan on agent start, delta on heartbeat | On start + every 30 seconds |
| Software | Package list comparison | Every heartbeat |
| Service | Service status polling | Every heartbeat |
| Network | Interface status check | Every heartbeat |

### Bandwidth Optimization

- Delta-based transmission ensures only changed data is sent.
- Inventory data is compressed before transmission.
- Full inventory snapshots are only sent on agent restart or when explicitly requested.

---

## Viewing Inventory in the Dashboard

### Global Inventory View

The dashboard provides a global inventory view across all agents.

**Via Dashboard:**
1. Navigate to the "Inventory" section in the main navigation.
2. The global view shows aggregated inventory data across all hosts.
3. Use the filter panel to narrow results by OS, host group, or specific inventory fields.

### Per-Agent Inventory

**Via Dashboard:**
1. Navigate to the agent grid and select an agent.
2. Open the "Inventory" tab in the agent detail view.
3. Switch between System, Software, Services, and Network sub-tabs.

### Inventory Search

The inventory supports full-text search across all collected data:

**API Endpoint:** `GET /api/v1/inventory/search?q={query}`

Search examples:
- Find all hosts running a specific software version
- Find all hosts with a particular network interface configuration
- Find all hosts where a specific service is stopped

### Inventory Comparison

Compare inventory between two agents or between two points in time:

**API Endpoint:** `GET /api/v1/inventory/compare?agent1={id1}&agent2={id2}`

This returns differences in system configuration, installed software, and running services between the two agents.

---

## Inventory API Reference

### List All Inventory

```
GET /api/v1/inventory
```

Returns aggregated inventory across all agents with optional filtering.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by inventory type: `system`, `software`, `services`, `network` |
| `agentId` | string | Filter by specific agent |
| `osType` | string | Filter by OS type |
| `search` | string | Full-text search query |
| `page` | integer | Pagination page number |
| `pageSize` | integer | Results per page (default: 50) |

### Get Agent Inventory

```
GET /api/v1/agents/{agentId}/inventory
```

Returns the full inventory for a specific agent.

### Get Inventory History

```
GET /api/v1/agents/{agentId}/inventory/history
```

Returns historical inventory changes for a specific agent, useful for tracking when software was installed or removed.

---

## Inventory Data Retention

| Data Type | Retention Period | Notes |
|-----------|-----------------|-------|
| Current inventory | Indefinite | Latest state always available |
| Inventory deltas | 90 days | Changed data retained for trend analysis |
| Full snapshots | 30 days | Snapshots taken on agent restart |
| Search index | Updated in real-time | Index rebuilt on server restart |

---

## Common Inventory Tasks

### Find Hosts Running Outdated Software

1. Navigate to Global Inventory > Software.
2. Search for the software package name.
3. Sort by version to identify outdated installations.
4. Use the agent list to plan upgrade scheduling.

### Verify Service Configuration After Change

1. Navigate to the affected agent's inventory.
2. Open the Services tab.
3. Filter for the specific service.
4. Verify status, start type, and running user match expectations.

### Audit Network Configuration

1. Navigate to Global Inventory > Network.
2. Filter by subnet or IP range.
3. Review interface configurations for compliance.
4. Export results for audit documentation.
