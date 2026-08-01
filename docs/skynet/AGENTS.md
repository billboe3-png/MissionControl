# AGENTS

## Responsibilities

Agents are lightweight, outbound-only daemons deployed on managed systems.
Their responsibilities are narrow and well-defined.

### Core Responsibilities
- Report health, telemetry, and inventory to Mission Control server
- Execute authorized commands dispatched by the server
- Plugin lifecycle: discover, initialize, collect, report
- Plugin sync: install missing authorized plugins on demand
- Maintain local state cache for offline resilience
- Rotate or report credential failures
- Emit structured operational visibility

## Heartbeat

Heartbeat is the cadence of trust.
Agents must:
- Send heartbeats within configured interval
- Include CPU, memory, disk, OS, active plugins
- Process server commands and plugin requests from response
- Treat repeated heartbeat failure as a critical condition

Heartbeat rules:
- Default interval: 30 seconds
- Max interval: 300 seconds without explicit override
- Failed heartbeats trigger retry with bounded backoff
- Three consecutive failures mark agent degraded in fleet state

## Inventory

Inventory collection covers:
- Operating system metadata
- Kernel and package state
- Docker containers
- Windows services and Hyper-V VMs
- Zabbix connectivity when configured
- AD and M365 metadata when configured
- Veeam and Proxmox metadata when configured

Inventory rules:
- Reports are timestamps
- Reports are JSON-structured
- Reports omit secrets from payloads
- Reports include plugin version and mode

## Command Execution

Agents execute commands:
- Dispatched by server only
- Scoped to agent’s authorized targets
- With bounded timeout and retry
- With result returned to server
- With stdout and stderr recorded in audit trail

Agents never:
- Initiate access to remote systems independently
- Store command credentials permanently
- Execute outside configured policy

## Offline Behavior

When disconnected:
- Queue command results
- Preserve local inventory cache
- Retry heartbeat on reconnect
- Never invent server state

Offline is normal.
Fleet state engine treats missing heartbeats as unknown, not failure.

## Caching

Caching:
- keeps latest inventory
- keeps pending commands during disconnect
- expires according to policy
- is replaced, not merged, on server reconnection

## Retry Logic

Retries are bounded and observable:
- exponential backoff with caps
- maximum retry counts explicit
- no silent end-of-retry success masking

Failed command execution results are queued, retried contextually, and reported.

## Fleet Management

Agents are members of fleets, not individuals.
Fleet-level operations:
- bulk command dispatch
- staged rollout
- plugin rollout
- policy application

Fleet rules:
- Agents never act on fleet commands directly
- Server mediates fleet actions
- Fleet changes are audited
- Fleet state is derived from heartbeat truth

## Security

Agent security:
- API key authentication only
- HTTP-only outbound calls
- Local-only plugin execution
- No inbound ports exposed
- System permissions minimized
- Filesystem access restricted
- Memory cleared of secrets after use

## Registration

Registration:
- Self-initiated outbound flow
- Assigned unique API key on registration
- API key encrypted in transit
- Returned once, never reissued without rotation event

## Updates

Updates:
- Triggered by server version check
- Applied via packaging toolchain
- Verified post-install
- Rolled back if health check fails
- Never force-updated outside maintenance window without operator approval

Agents never auto-update to unreleased or unsigned artifacts.

## Why Agents Remain Lightweight

Agents remain lightweight because:
- they are deployed at scale
- they run on constrained systems
- they must remain auditable and inspectable
- they must recover quickly from failure

Complexity belongs in the server.
Simplicity belongs in agents.

## Why the Server Always Remains Authoritative

The server is authoritative because:
- it sees all agents
- it holds the policy
- it maintains persisted truth
- it can resolve conflicts between agent facts
- it enforces rollback and approval
- it never has local file-system bias

Agents are executors.
Servers are truth sources.

```text
AGENT: collects and obeys
SERVER: decides and records
```

Never invert this relationship.
