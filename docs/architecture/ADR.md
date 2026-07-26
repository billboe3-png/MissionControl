# Mission Control — Architecture Decision Records

**Version:** 3.0.0

---

## Overview

Architecture Decision Records (ADRs) document significant architectural decisions. Each ADR captures the context, decision, and consequences.

---

## ADR-001: Agent-First Architecture

**Date:** 2026-07-26
**Status:** Accepted
**Deciders:** Mission Control Team

### Context

Mission Control needs to collect infrastructure data from managed servers. The traditional approach is for the server to poll infrastructure directly (SSH/WinRM). This creates scalability, security, and reliability problems.

### Decision

All infrastructure data flows through agents. The server never initiates connections to managed infrastructure when an agent is available. SSH/WinRM become fallback-only for devices that cannot run agents.

### Consequences

**Positive:**
- Agents can operate offline and queue data
- No inbound firewall rules needed on managed servers
- Agent-first is more scalable (each agent handles its own network)
- Agents can relay data from remote targets

**Negative:**
- Requires agent installation on every managed server
- Adds complexity to the agent codebase
- Server cannot directly verify infrastructure state

---

## ADR-002: Plugin-First Design

**Date:** 2026-07-26
**Status:** Accepted
**Deciders:** Mission Control Team

### Context

IT infrastructure is diverse. No single platform can natively support every technology. Hard-coding integrations creates maintenance burden and limits extensibility.

### Decision

The core platform provides authentication, scheduling, and orchestration. All infrastructure knowledge lives in plugins. Each integration (Hyper-V, Proxmox, Zabbix, Veeam, AD, M365) is a plugin.

### Consequences

**Positive:**
- New integrations can be added without modifying core code
- Plugins can be enabled/disabled per deployment
- Community can contribute plugins
- Marketplace for plugin discovery

**Negative:**
- Plugin interface must be stable and well-documented
- Plugin quality varies (marketplace governance needed)
- More complex than monolithic architecture

---

## ADR-003: Heartbeat Communication

**Date:** 2026-07-26
**Status:** Accepted
**Deciders:** Mission Control Team

### Context

Agents need to communicate with the server. Options include: server polls agents, agents poll server, push from agents, or agent-initiated bidirectional.

### Decision

Agents initiate all communication via heartbeat requests every 30 seconds. The server responds with pending commands and configuration. This is agent-initiated bidirectional communication.

### Consequences

**Positive:**
- No inbound connections to agents needed
- Server can adjust heartbeat frequency
- Commands are delivered efficiently (piggyback on heartbeat)
- Natural offline detection (no heartbeat = offline)

**Negative:**
- 30-second delay for command delivery
- Server cannot push urgent commands instantly
- Multiple agents increase server load

---

## ADR-004: Event-Driven Architecture

**Date:** 2026-07-26
**Status:** Accepted
**Deciders:** Mission Control Team

### Context

Components need to communicate state changes. Direct method calls create tight coupling between components.

### Decision

Components communicate through an internal event bus. Publishers emit events, subscribers react independently. No direct method calls between unrelated services.

### Consequences

**Positive:**
- Loose coupling between components
- Easy to add new subscribers
- Error isolation (one failing handler doesn't affect others)
- Clear audit trail of state changes

**Negative:**
- In-process only (single server limitation)
- Debugging is harder (indirect communication)
- Event ordering may vary

---

## ADR-005: Single Codebase for Community and Enterprise

**Date:** 2026-07-26
**Status:** Accepted
**Deciders:** Mission Control Team

### Context

Open-source projects often fork into community and enterprise editions, creating maintenance burden and divergence.

### Decision

Community and Enterprise share one codebase. The `EDITION` configuration flag controls feature availability. No code forks.

### Consequences

**Positive:**
- One codebase to maintain
- Enterprise features benefit from community testing
- Easy migration from community to enterprise
- No merge conflicts between editions

**Negative:**
- Enterprise features must be gated, not hidden
- Configuration complexity increases
- Documentation must cover both editions

---

## ADR-006: Fallback SSH/WinRM Execution

**Date:** 2026-07-26
**Status:** Accepted
**Deciders:** Mission Control Team

### Context

Some infrastructure (switches, firewalls, embedded devices) cannot run agents. These devices require direct remote execution.

### Decision

SSH and WinRM providers are retained as fallback mechanisms. When no agent is available for a target, the server falls back to direct SSH/WinRM execution.

### Consequences

**Positive:**
- Supports devices that cannot run agents
- Gradual migration path (agent-first when possible)
- Preserves existing SSH/WinRM investment

**Negative:**
- Requires inbound firewall rules for SSH/WinRM
- Credential management for direct connections
- Two execution paths to maintain

---

## ADR-007: Dashboard Aggregator Pattern

**Date:** 2026-07-26
**Status:** Accepted
**Deciders:** Mission Control Team

### Context

The dashboard needs data from many sources. Direct database queries from the dashboard create tight coupling and duplicated logic.

### Decision

The dashboard delegates to domain services. It never queries the database directly. Each domain service provides a `get_dashboard_summary()` method.

### Consequences

**Positive:**
- Single point of contact for the frontend
- Domain services own their data access logic
- Easy to add new dashboard widgets
- Frontend isolated from backend changes

**Negative:**
- Extra method calls (performance overhead)
- Each service must implement dashboard summary
- Dashboard response format must be stable

---

## ADR-008: Configuration Over Forks

**Date:** 2026-07-26
**Status:** Accepted
**Deciders:** Mission Control Team

### Context

Customizing deployments often leads to code forks, which create maintenance burden and divergence from upstream.

### Decision

Features are enabled/disabled through configuration, not code modifications. The `Settings` class (42 fields) controls all behavior.

### Consequences

**Positive:**
- One codebase for all deployments
- Easy to switch between configurations
- No merge conflicts from customization
- Clear upgrade path

**Negative:**
- Configuration complexity
- Some features may be awkward to configure
- Must support all configuration combinations
