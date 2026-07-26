# Disaster Recovery Procedures

**Purpose:** Backup, recovery, failover, and data integrity procedures  
**Related:** [MAINTENANCE.md](./MAINTENANCE.md), [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md), [AGENTS.md](./AGENTS.md), [REPORTING.md](./REPORTING.md)

---

## Disaster Recovery Overview

This document defines the procedures for backing up Mission Control data, recovering from failures, and maintaining business continuity. The disaster recovery plan covers data backups, system recovery, failover procedures, and data integrity verification.

---

## RTO/RPO Targets

| System Component | RTO (Recovery Time Objective) | RPO (Recovery Point Objective) |
|-----------------|-------------------------------|-------------------------------|
| Mission Control API | 1 hour | 5 minutes |
| Mission Control Database | 1 hour | 5 minutes |
| Agent Network | 2 hours | 30 minutes |
| Automation System | 1 hour | 5 minutes (playbook definitions) |
| Plugin System | 2 hours | 24 hours (plugin configurations) |
| Event Bus | 30 minutes | 0 (event replay from log) |
| Inventory Data | 4 hours | 24 hours |
| Audit Trail | 1 hour | 0 (write-ahead log) |
| Remote Operations Config | 1 hour | 24 hours |

---

## Backup Schedule

### Backup Types

| Backup Type | Frequency | Retention | Storage |
|-------------|-----------|-----------|---------|
| Full database backup | Daily at 01:00 UTC | 30 days | Local + offsite |
| Incremental database backup | Every 6 hours | 7 days | Local + offsite |
| Configuration backup | Daily at 03:00 UTC | 90 days | Local + offsite |
| Playbook definitions backup | Daily at 03:00 UTC | 90 days | Local + offsite |
| Certificate backup | Weekly on Sunday | 1 year | Encrypted offsite |
| Agent registration data | Daily at 01:00 UTC | 30 days | Local + offsite |
| Audit trail export | Weekly on Sunday | 1 year | Encrypted offsite |

### Backup Storage Locations

| Location | Purpose | Access |
|----------|---------|--------|
| Local backup server | Fast recovery for recent backups | Direct access from Mission Control server |
| Offsite storage | Disaster recovery if primary site is lost | Secure transfer required |
| Cloud storage (encrypted) | Long-term retention and geographic redundancy | Encrypted, access-controlled |

### Backup Configuration

#### Database Backups

**Playbook:** `Database Backup - Daily Full`  
**Schedule:** Daily at 01:00 UTC

1. **Pre-backup check**
   - Verify database is running and accessible.
   - Check available disk space for backup files.
   - Verify backup storage location is accessible.

2. **Execute backup**
   - Create a full database dump with compression.
   - Generate a checksum for integrity verification.
   - Log the backup start time, end time, and file size.

3. **Post-backup verification**
   - Verify the backup file exists and is non-empty.
   - Validate the checksum.
   - Test restore to a temporary location (weekly).
   - Copy backup to offsite storage.

4. **Cleanup**
   - Remove backups older than the retention period.
   - Update the backup manifest.

#### Configuration Backups

**Playbook:** `Configuration Backup - Daily`  
**Schedule:** Daily at 03:00 UTC

**Configuration items backed up:**

| Item | Source | Description |
|------|--------|-------------|
| Mission Control configuration | Server config files | Core platform settings |
| API configuration | Server config files | API endpoints, auth settings |
| Agent configurations | Database | All agent registration data |
| Plugin configurations | Plugin store | All plugin settings |
| Playbook definitions | Database | All playbook definitions |
| Schedule definitions | Database | All automation schedules |
| Credential references | Encrypted store | Credential metadata (not secrets) |
| Notification rules | Database | Alert notification configuration |

---

## Recovery Procedures

### Scenario 1: Database Corruption

**Impact:** Mission Control API cannot read/write data  
**RTO:** 1 hour  
**RPO:** 5 minutes (last incremental backup)

#### Recovery Steps

1. **Assess the damage**
   - Check database error logs for corruption details.
   - Determine if the corruption is localized or widespread.
   - Check if recent backups are available and valid.

2. **Stop the Mission Control service**
   - Gracefully stop the API service to prevent further damage.
   - Verify all connections are closed.

3. **Restore from backup**
   - Identify the most recent valid backup (check checksums).
   - Restore the database from the backup.
   - Apply any incremental backups if available and not corrupted.

4. **Verify data integrity**
   - Run database consistency checks.
   - Verify critical data (agent registrations, alert history, audit trail).
   - Check for any data gaps between the backup and the failure point.

5. **Restart the service**
   - Start the Mission Control API service.
   - Verify API endpoints are responding.
   - Check agent connectivity is restored.

6. **Post-recovery**
   - Document the incident per [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md).
   - Identify the root cause of the corruption.
   - Implement preventive measures.

### Scenario 2: Mission Control Server Failure

**Impact:** Complete loss of Mission Control platform  
**RTO:** 1 hour  
**RPO:** 5 minutes

#### Recovery Steps

1. **Provision a new server**
   - Deploy a new server with the same specifications.
   - Install the Mission Control application.
   - Configure network connectivity.

2. **Restore configuration**
   - Retrieve the most recent configuration backup from offsite storage.
   - Restore the configuration to the new server.
   - Update any server-specific settings (IP addresses, hostnames).

3. **Restore database**
   - Retrieve the most recent database backup from offsite storage.
   - Restore the database to the new server.
   - Apply incremental backups if available.

4. **Restore certificates**
   - Retrieve certificates from the encrypted backup.
   - Install certificates on the new server.
   - Verify certificate validity.

5. **Start the service**
   - Start the Mission Control API service.
   - Verify all endpoints are responding.
   - Update DNS records if the server IP has changed.

6. **Reconnect agents**
   - Agents will automatically reconnect on their next heartbeat (30 seconds).
   - Verify agents are transitioning to `online` state.
   - For agents that do not reconnect, check network connectivity and configuration.

7. **Verify operations**
   - Check dashboard data is populating correctly.
   - Verify automation is functioning.
   - Test alert generation and notification.
   - Confirm plugin health.

### Scenario 3: Agent Network Failure

**Impact:** Loss of monitoring for managed hosts  
**RTO:** 2 hours  
**RPO:** 30 minutes

#### Recovery Steps

1. **Assess the scope**
   - Determine how many agents are affected.
   - Identify if the failure is localized (single host) or widespread (network).

2. **For localized failures**
   - Check the affected host's network connectivity.
   - Verify the agent process is running.
   - Restart the agent process if needed.
   - Check firewall rules.

3. **For widespread failures**
   - Check the Mission Control server's network connectivity.
   - Verify the agent communication endpoint is accessible.
   - Check for network infrastructure issues.
   - Contact the network team if needed.

4. **For total agent loss**
   - If the Mission Control server is unreachable, agents will continue operating locally.
   - Agents buffer their data and will sync when connectivity is restored.
   - No data loss occurs during agent network outages.

5. **Verify recovery**
   - Monitor agent states as they transition back to `online`.
   - Verify inventory data is being collected.
   - Check that any buffered data is synced.

### Scenario 4: Plugin System Failure

**Impact:** Loss of extended functionality  
**RTO:** 2 hours  
**RPO:** 24 hours

#### Recovery Steps

1. **Identify the failing plugin**
   - Check plugin health status in the dashboard.
   - Review plugin error logs.

2. **Disable the failing plugin**
   - Disable the plugin to prevent further errors.
   - Verify other plugins are not affected.

3. **Restore plugin configuration**
   - If configuration is corrupted, restore from backup.
   - Reconfigure any custom settings.

4. **Reinstall the plugin**
   - If the plugin binary is corrupted, reinstall from the marketplace.
   - Restore the configuration.
   - Enable the plugin.

5. **Verify functionality**
   - Check plugin health status is `healthy`.
   - Test the plugin's core functionality.
   - Monitor for recurring errors.

---

## Failover Procedures

### Automatic Failover

Mission Control supports automatic failover for critical components.

#### Database Failover

| Setting | Value |
|---------|-------|
| Primary | Main database server |
| Replica | Standby database server |
| Replication | Synchronous |
| Failover trigger | Primary unreachable for 30 seconds |
| Failover method | Automatic with manual confirmation |

#### Event Bus Failover

| Setting | Value |
|---------|-------|
| Primary | Primary event bus instance |
| Backup | Secondary event bus instance |
| Replication | Asynchronous with persistence |
| Failover trigger | Primary processing delay > 5 seconds |

### Manual Failover

When automatic failover is not available or not appropriate:

1. **Assess the situation** — confirm the primary is truly failed.
2. **Notify stakeholders** — inform the team of the failover.
3. **Execute the failover** — follow the component-specific failover procedure.
4. **Verify the backup is operational** — confirm the new primary is functioning.
5. **Update routing** — ensure traffic is directed to the new primary.
6. **Monitor** — watch for any issues in the new configuration.
7. **Document** — record the failover event and any issues encountered.

### Failback Procedures

After the primary system is restored:

1. **Verify primary health** — confirm the original primary is fully functional.
2. **Sync data** — ensure all data is synchronized from the current primary to the restored primary.
3. **Schedule failback** — choose a low-impact window for failback.
4. **Execute failback** — switch traffic back to the original primary.
5. **Verify operations** — confirm everything is functioning normally.
6. **Monitor** — watch closely for 24 hours after failback.

---

## Data Integrity Checks

### Automated Integrity Checks

| Check | Frequency | Method |
|-------|-----------|--------|
| Database consistency | Daily | Automated script |
| Backup checksum validation | On backup creation | SHA-256 checksum |
| Audit trail integrity | Continuous | Write-ahead log verification |
| Configuration hash verification | Daily | Hash comparison |
| Agent data integrity | Every heartbeat | Checksum validation |

### Manual Integrity Checks

Perform these checks during the monthly infrastructure review:

1. **Database integrity**
   - Run full database consistency check.
   - Review any orphaned records.
   - Verify foreign key constraints.

2. **Backup integrity**
   - Test restore of a random backup to a temporary location.
   - Verify the restored data is consistent and complete.
   - Check that all expected tables and records are present.

3. **Configuration integrity**
   - Compare current configuration against the last backup.
   - Verify no unauthorized changes have been made.
   - Check that all expected configuration items are present.

4. **Audit trail integrity**
   - Verify the audit trail has no gaps.
   - Check that write-ahead log entries are consistent.
   - Verify that no entries have been tampered with.

### Integrity Check Report

Each integrity check produces a report:

| Field | Description |
|-------|-------------|
| `checkDate` | When the check was performed |
| `checkType` | What was checked |
| `status` | `pass`, `fail`, or `warning` |
| `details` | Specific findings |
| `recommendedActions` | Suggested follow-up actions |

---

## Disaster Recovery Testing

### Monthly DR Test

**Schedule:** Last Friday of each month, 14:00 UTC  
**Duration:** Up to 4 hours  
**Participants:** Operations team + Infrastructure Lead

#### Test Procedure

1. **Pre-test preparation**
   - Verify all backups are current.
   - Notify stakeholders of the DR test.
   - Document the current system state.

2. **Scenario execution**
   - Select a DR scenario to test (rotate through the scenarios).
   - Execute the recovery procedure for that scenario.
   - Time each step against the RTO target.

3. **Validation**
   - Verify the recovered system is fully functional.
   - Check that agents reconnect successfully.
   - Test automation execution.
   - Verify data integrity.

4. **Cleanup**
   - Restore the original system state.
   - Verify normal operations resume.
   - Clean up any test artifacts.

5. **Documentation**
   - Record the test results.
   - Document any issues or delays.
   - Update procedures based on lessons learned.

### DR Test Scenarios Rotation

| Month | Scenario | Key Focus |
|-------|----------|-----------|
| January | Database corruption recovery | Backup restoration speed |
| February | Server failure recovery | Full platform restoration |
| March | Agent network failure | Monitoring continuity |
| April | Plugin system failure | Extended functionality recovery |
| May | Full site failover | Complete DR activation |
| June | Data integrity verification | Comprehensive integrity checks |
| July | Database corruption recovery | (repeat cycle) |
| August | Server failure recovery | (repeat cycle) |
| September | Agent network failure | (repeat cycle) |
| October | Plugin system failure | (repeat cycle) |
| November | Full site failover | (repeat cycle) |
| December | Year-end comprehensive test | All scenarios in sequence |

### DR Test Metrics

Track these metrics across tests:

| Metric | Target | Description |
|--------|--------|-------------|
| Actual RTO | Within 150% of target | Time to recover |
| Actual RPO | Within target | Data loss amount |
| Success rate | 100% | Percentage of tests that fully succeed |
| Issues found | Decreasing trend | Number of issues discovered |
| Procedure accuracy | Increasing trend | Percentage of steps that worked as documented |

---

## Emergency Contacts

| Role | Primary Contact | Backup Contact | When to Contact |
|------|----------------|----------------|-----------------|
| Infrastructure Lead | Defined in team roster | Platform Engineering Lead | DR activation, server failure |
| Database Administrator | Defined in team roster | Infrastructure Lead | Database corruption, data loss |
| Network Engineer | Defined in team roster | Infrastructure Lead | Network failure, connectivity issues |
| Security Team | Defined in security policy | Infrastructure Lead | Security-related DR events |
| Executive Sponsor | Defined in leadership roster | Infrastructure Lead | Extended outages, business impact |

---

## Disaster Recovery Checklist

Use this checklist when activating disaster recovery:

- [ ] Incident declared as disaster
- [ ] DR team assembled
- [ ] Stakeholders notified
- [ ] Current system state documented
- [ ] Backup integrity verified
- [ ] Recovery scenario selected
- [ ] Recovery procedure initiated
- [ ] Each step timed and documented
- [ ] Recovery validated
- [ ] Data integrity verified
- [ ] Agents reconnected (if applicable)
- [ ] Automation verified functional
- [ ] Plugins verified healthy
- [ ] Normal operations confirmed
- [ ] Stakeholders notified of recovery
- [ ] Post-DR review scheduled
- [ ] Documentation updated
