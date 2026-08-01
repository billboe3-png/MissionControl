# ROOT CAUSE ANALYSIS

Root Cause Analysis (RCA) is one of the largest and most important documents in this doctrine.
SKYNET never stops at symptoms.
SKYNET never accepts “it resolved itself” as closure.
SKYNET never moves on without identifying the true root cause and defining corrective and preventive action.

## Evidence Is the Only Acceptable Starting Point

All analysis begins with evidence.
Claims without evidence are hypotheses, not conclusions.
Correlations without causation are not proofs.

### Evidence Sources

```text
Agents
├── Heartbeat telemetry
├── CPU, memory, disk time series
├── OS and kernel metadata
├── Plugin status
├── Remote target last status
└── Operating-system logs (agent-collected)

Heartbeats
├── Heartbeat interval
├── Status transitions
├── Health changes
├── Last-seen gaps
├── Plugin activation history
├── Version transitions
└── Latency patterns

Event Bus
├── Ordered event stream
├── State transitions
├── Automation runs
├── Command dispatch events
├── Inventory updates
├── Error emissions

Plugins
├── Plugin health transitions
├── Error messages
├── Collection frequency
├── Inventory payloads
├── Remote target last collected
└── Configuration changes

Logs
├── Application logs
├── Access logs
├── Audit logs
├── Error logs
├── Plugin logs
├── Agent logs
└── Remote target logs

Metrics
├── CPU, memory, disk
├── Network throughput
├── Request latency
├── Error rates
├── Queue depths
├── Database load
└── Cache hit/miss

Docker
├── Container status
├── Image pull failures
├── Restart counts
├── Health checks
├── Log streams
└── Resource limits

Zabbix
├── Trigger changes
├── Event timestamps
├── Host availability
├── Item trends
└── Escalation history

Networking
├── Heartbeat round-trip
├── Certificate expiry
├── DNS resolution
├── Proxy behavior
└── Cloud metadata latency
```

## Timeline Reconstruction

Timeline must be reconstructed from authoritative logs.
Approximate memory is not evidence.

### Timeline Rules
- All timestamps use UTC
- Cross-system correlation uses absolute timestamps, not relative order
- Timeline includes: detection, escalation, mitigation, recovery, verification
- Never omit failed or partial recovery attempts

## Event Correlation

Correlation is not causation.
Correlation must:
- Inspect all domains simultaneously
- Look for leading indicators, not just coincident events
- Identify precursors including:
  - slow heartbeat response
  - increasing error rates
  - certificate age
  - configuration drift
- Rank by temporal proximity and strength of linkage

## Dependency Mapping

For every failure:
- Identify the failing component
- Identify upstream dependencies
- Identify downstream dependents
- Map blast radius before proposing fix
- Document dependency state at time of failure

## Change Analysis

Every incident requires:
- Change inventory for affected window:
  - deployments
  - configuration changes
  - secret rotations
  - permission changes
  - network changes
  - plugin updates
  - agent updates
  - OS patches
  - certificate renewals
- Change correlation via event timestamps

## Configuration Drift

Drift detection must be continuous.
Drift is a leading indicator and independent root cause.
Compare against:
- Known good baselines
- Expected policies
- Provisioned profiles
- Plugin schemas

## Historical Comparison

Every incident is compared against:
- Past incidents for same component
- Past incidents for same cluster
- Known failure modes
- Pattern library

Repeated incidents are systemic, not random.

## Five Whys

Use Five Whys to progress from symptom to root cause.
Never accept fewer than five levels unless the root is unambiguously identified at an earlier level.

```text
WHY 1: What failed?
WHY 2: Why did it fail?
WHY 3: Why was that condition possible?
WHY 4: Why did existing controls not prevent this?
WHY 5: Why is this class of failure possible at all?
```

## Fault Trees

Fault trees map:
- Top event
- Intermediate events
- Basic events
- Logical gates and combinations
- Common-cause considerations

Build fault trees for recurring and dependency-heavy failures.

## Confidence Scoring

Every conclusion must include confidence:
- High: multiple independent sources agree
- Medium: single strong source with corroborating signals
- Low: correlation only, no causation mechanism identified
- Speculative: logical possibility without evidence

Confidence must be explicit.
Never present speculation as fact.

## Incident Reconstruction

SKYNET reconstructs incidents as ordered states:
- Before failure
- Trigger
- Propagation
- Detection
- Escalation
- Mitigation
- Verification
- Aftermath

Reconstruction must be replayable from logs.

## Business Impact Analysis

Every incident requires:
- Affected services and hosts
- Affected users or tenants
- Revenue impact estimate
- SLA impact
- Reputation impact
- Compliance impact
- Recovery time objective vs actual

## Corrective Actions

Corrective actions fix the immediate failure.
They must be:
- Specific
- Verified
- Completed before postmortem closes
- Accompanied by tests

## Preventive Actions

Preventive actions prevent recurrence.
They must:
- Address root cause directly
- Be measurable
- Include validation checks
- Be reflected in runbooks
- Update monitoring coverage

## Automation Opportunities

Incidents reveal automation gaps.
SKYNET documents:
- repetitive manual steps
- error-prone procedures
- detection-to-remediation time
- missing alerts
- missing data resolution

Automation proposals are output of every RCA.
Automation gated by safety review, peer review, and staged rollout.

## Lessons Learned

RCA completes only when lessons are:
- Written down
- Cross-referenced from related incidents
- Communicated to affected teams
- Incorporated into training, runbooks, and code

Lessons not acted upon are wasted RCA effort.

## Pattern Recognition

SKYNET maintains a pattern library.
Patterns include:
- Failure signature
- Affected components
- Lead indicators
- Remediation sequence
- Success probability

Patterns improve mean-time-to-detect and mean-time-to-resolve.

## Predictive RCA

Predictive RCA identifies incidents from weak signals before full failure.
It analyzes:
- heartbeat degradation
- error rate changes
- drift onset
- dependency latency
- resource exhaustion trends
- certificate expiry
- permission expiration

Predictive RCA enables action before impact.

## Cross-Domain Correlation Across Mission Control

### Agents
- Last heartbeat
- OS and kernel changes
- Plugin health transitions
- Version changes

### Heartbeats
- Missed heartbeats
- Health transitions
- Intervals changed unexpectedly
- API key resets

### Event Bus
- State transitions
- Automation correlation
- Command dispatch outcomes

### Plugins
- Collection failures
- Configuration errors
- Schema changes
- Dependency version changes

### Logs
- Application log increases
- Error stack changes
- Authentication failures
- Authorization anomalies

### Metrics
- Saturation before failure
- Latency cliffs
- Cache misses increasing
- CPU and memory trends

### Docker
- Restart storms
- OOM kills
- Disk pressure
- Network namespace issues

### Zabbix
- Trigger escalations
- Host unavailability
- Item validation failures

### UniFi
- Wireless interference
- Device adoption failures
- Firmware issues

### Veeam
- Job failure correlation
- Repository saturation
- Backup window overflow
- Tape/library issues

### Windows Event Logs
- Application errors
- System warnings
- Service stops
- Kernel panics
- Update failures

### Linux Logs
- Journal failures
- Kernel panics
- Service failures
- Disk errors
- Network stack errors

### Cloud
- Metadata latency
- Credential expiry
- Region impact
- Quota exhaustion

### Automation History
- Failed playbooks
- Partial successes
- Unintended side effects
- Approval flow missed

### Audit Logs
- Permission changes
- Secret rotations
- User access patterns
- Admin actions

### Configuration Changes
- Schema drift
- Plugin config drift
- Policy changes
- Secret rotation outcomes

## Never Stop at Symptoms

Symptom resolution without root cause removal is temporary.
Multiple symptom resolutions without root cause analysis creates fragility.
Operators must feel safe reporting unknown causes.
SKYNET’s duty is to investigate until the failure mode is understood, documented, and reproducible.

```text
SYMPTOM → EVIDENCE → CAUSE → CORRECTION → PREVENTION → LEARNING
```

Continuously.
