# Scheduled Maintenance Guide

**Purpose:** Performing and managing scheduled maintenance tasks  
**Related:** [AUTOMATION.md](./AUTOMATION.md), [PLAYBOOKS.md](./PLAYBOOKS.md), [AGENTS.md](./AGENTS.md), [PLUGINS.md](./PLUGINS.md), [DISASTER_RECOVERY.md](./DISASTER_RECOVERY.md)

---

## Maintenance Overview

Regular maintenance ensures the continued reliability and performance of Mission Control and the infrastructure it manages. This guide covers all scheduled maintenance procedures.

---

## Maintenance Schedule

| Task | Frequency | Window | Duration | Responsible |
|------|-----------|--------|----------|-------------|
| Database maintenance | Weekly | Sunday 02:00-04:00 UTC | 30 minutes | Platform Engineering |
| Log rotation | Daily | 00:00 UTC | 5 minutes | Automated |
| Certificate renewal check | Weekly | Monday 09:00 UTC | 15 minutes | Operations |
| Plugin updates | Monthly | First Saturday 06:00 UTC | 1 hour | Operations |
| Agent updates | Monthly | First Saturday 06:00 UTC | 2 hours | Operations |
| System health check | Daily | 07:00 UTC | 10 minutes | Automated |
| Full infrastructure review | Monthly | First Monday 10:00 UTC | 2 hours | Operations Lead |
| Disaster recovery test | Monthly | Last Friday 14:00 UTC | 4 hours | Operations + Infrastructure |

---

## Database Maintenance

### Weekly Database Maintenance

**Schedule:** Sunday 02:00-04:00 UTC  
**Playbook:** `Database Maintenance - Weekly`

#### Maintenance Tasks

1. **Vacuum and optimize**
   - Reclaim wasted space from deleted records
   - Optimize table structures
   - Estimated time: 10-15 minutes

2. **Index rebuild**
   - Rebuild fragmented indexes
   - Update index statistics
   - Estimated time: 10-15 minutes

3. **Data purge**
   - Remove expired data based on retention policies
   - Purge old heartbeat deltas (older than 90 days)
   - Purge old inventory snapshots (older than 30 days)
   - Purge resolved alerts (older than 180 days)
   - Estimated time: 5-10 minutes

4. **Consistency check**
   - Verify database integrity
   - Check for orphaned records
   - Validate foreign key constraints
   - Estimated time: 5-10 minutes

5. **Backup verification**
   - Verify the latest backup is valid
   - Test restore to staging environment (monthly)
   - Estimated time: 5 minutes (weekly), 30 minutes (monthly)

#### Monitoring the Maintenance

After the maintenance completes:
1. Review the maintenance execution log for errors.
2. Verify the database size has been reduced (if purge ran).
3. Check API response times to confirm performance improvement.
4. Review application logs for any database-related errors.

---

## Log Rotation

### Daily Log Rotation

**Schedule:** Daily at 00:00 UTC  
**Method:** Automated via OS-level logrotate configuration

#### Log Rotation Configuration

| Log Source | Retention | Max Size | Compression |
|------------|-----------|----------|-------------|
| Application logs | 30 days | 100 MB per file | gzip |
| Agent logs | 14 days | 50 MB per file | gzip |
| API access logs | 90 days | 200 MB per file | gzip |
| Audit logs | 365 days | 500 MB per file | gzip |
| Database logs | 30 days | 100 MB per file | gzip |
| Plugin logs | 14 days | 50 MB per file | gzip |

#### Log Locations

| Log Type | Default Location |
|----------|-----------------|
| Application logs | `/var/log/missioncontrol/` |
| Agent logs | Agent-specific directory on each host |
| API access logs | `/var/log/missioncontrol/api/` |
| Audit logs | `/var/log/missioncontrol/audit/` |
| Database logs | Database engine default location |

#### Verifying Log Rotation

After log rotation runs:
1. Verify that old log files have been compressed and archived.
2. Confirm that current log files have been rotated.
3. Check that disk usage has been reduced.
4. Verify that logging continues normally in the new log files.

---

## Certificate Renewal

### Weekly Certificate Check

**Schedule:** Monday 09:00 UTC  
**Playbook:** `Certificate Check - Weekly`

#### Certificates to Monitor

| Certificate | Location | Renewal Lead Time | Auto-Renewal |
|-------------|----------|-------------------|--------------|
| Mission Control API TLS | Server | 30 days | Yes (Let's Encrypt) |
| Agent-server mTLS | Agent | 90 days | No |
| Plugin API keys | Plugin config | Varies | No |
| External service tokens | Configuration | Varies | Varies |

#### Certificate Check Procedure

1. **Run the certificate check playbook** to scan all certificates.
2. **Review the report** for certificates expiring within the next 30 days.
3. **For auto-renewed certificates:** Verify the renewal completed successfully.
4. **For manual renewal certificates:** Initiate the renewal process.
5. **Update certificates** that have been renewed.
6. **Test connectivity** after certificate updates.

#### Certificate Renewal Steps

**TLS Certificate (Let's Encrypt):**
1. Verify certbot or ACME client is installed.
2. Run: `certbot renew --dry-run` to test renewal.
3. Run: `certbot renew` to perform actual renewal.
4. Verify the new certificate is in place.
5. Restart the web server or reverse proxy.
6. Test HTTPS connectivity.

**Agent mTLS Certificate:**
1. Generate a new certificate signing request (CSR).
2. Submit the CSR to your internal CA.
3. Receive the signed certificate.
4. Update the agent configuration with the new certificate.
5. Restart the agent process.
6. Verify agent heartbeat resumes normally.

---

## Plugin Updates

### Monthly Plugin Update

**Schedule:** First Saturday of each month, 06:00 UTC  
**Playbook:** `Plugin Update - Monthly`

#### Update Procedure

1. **Pre-update check**
   - Review available updates in the marketplace.
   - Check release notes for breaking changes.
   - Verify compatibility with the current Mission Control version.
   - Document current plugin versions.

2. **Backup configuration**
   - Export the current configuration for each plugin.
   - Note any custom configuration values.

3. **Update plugins one at a time**
   - Update the plugin via the marketplace.
   - Wait for the update to complete.
   - Verify plugin health status is `healthy`.
   - Check that the plugin is functioning correctly.
   - Proceed to the next plugin.

4. **Post-update verification**
   - Verify all plugins are active and healthy.
   - Test key plugin functionality.
   - Review plugin logs for errors.
   - Monitor for 24 hours after the update.

#### Rollback Procedure

If a plugin update causes issues:
1. Disable the problematic plugin immediately.
2. Review the error logs to identify the issue.
3. If the issue is a regression, reinstall the previous version.
4. Re-enable the plugin and verify functionality.
5. Document the issue and report to the plugin author.

---

## Agent Updates

### Monthly Agent Update

**Schedule:** First Saturday of each month, 06:00 UTC  
**Playbook:** `Agent Update - Monthly`

#### Update Strategy

Agent updates are performed in batches to minimize risk:

| Batch | Hosts | Percentage | Wait Time |
|-------|-------|------------|-----------|
| 1 | Development/test hosts | ~10% | 30 minutes |
| 2 | Non-production staging hosts | ~20% | 1 hour |
| 3 | Production hosts (low priority) | ~30% | 2 hours |
| 4 | Production hosts (high priority) | ~40% | Monitor for 24 hours |

#### Update Procedure

1. **Pre-update inventory**
   - Document current agent versions across all hosts.
   - Verify all agents are currently healthy.
   - Ensure no critical alerts are active.

2. **Batch 1: Development/test hosts**
   - Update agents on development and test hosts.
   - Wait for batch completion.
   - Verify all agents return to `online` or `healthy` state.
   - Test basic agent functionality.
   - If issues are found, stop the update process and investigate.

3. **Batch 2: Staging hosts**
   - Update agents on non-production staging hosts.
   - Wait and verify as above.

4. **Batch 3: Production hosts (low priority)**
   - Update agents on low-priority production hosts.
   - Wait and verify as above.

5. **Batch 4: Production hosts (high priority)**
   - Update agents on high-priority production hosts.
   - Monitor closely for 24 hours.

6. **Post-update verification**
   - Verify all agents are reporting correctly.
   - Review agent health history for regressions.
   - Check inventory data is being collected normally.

#### Agent Update Rollback

If an agent update causes issues:
1. Identify the affected agents.
2. Disable the problematic update if possible.
3. Revert to the previous agent version.
4. Verify agent functionality is restored.
5. Document the issue and investigate the root cause.

---

## System Health Checks

### Daily Health Check

**Schedule:** Daily at 07:00 UTC  
**Method:** Automated via scheduled playbook

#### Health Check Items

| Check | What to Verify | Threshold |
|-------|---------------|-----------|
| API availability | API endpoint responds | < 500ms response time |
| Database connectivity | Database queries execute | < 100ms average query time |
| Agent connectivity | All expected agents are online | 100% expected agents online |
| Disk space | Server disk usage | < 80% used |
| Memory usage | Server memory usage | < 85% used |
| CPU usage | Server CPU usage | < 80% average |
| Certificate status | All certificates valid | > 14 days until expiry |
| Plugin health | All plugins healthy | 0 plugins in error state |
| Event bus | Event processing running | < 1 second processing delay |
| Log volume | Log ingestion rate normal | Within 200% of baseline |

#### Health Check Results

The daily health check produces a report with:
- Overall status (pass/fail for each check)
- Trend data (is each metric improving, stable, or degrading)
- Action items (any issues that need attention)

#### Responding to Health Check Failures

1. Review the health check report as part of the daily morning routine.
2. For any failed checks, investigate immediately.
3. Create an alert if the failure indicates a developing incident.
4. Track recurring health check failures for capacity planning.

---

## Maintenance Window Management

### Scheduling Maintenance

When scheduling maintenance that affects services:

1. **Create a maintenance ticket** in your ticketing system.
2. **Notify stakeholders** at least 48 hours in advance (24 hours for emergency maintenance).
3. **Update the status page** if customer-facing.
4. **Execute the maintenance** during the approved window.
5. **Verify completion** and update the ticket.
6. **Close the maintenance window** and notify stakeholders.

### Emergency Maintenance

For emergency maintenance that cannot wait for a scheduled window:

1. **Assess the urgency** — is this truly an emergency?
2. **Notify stakeholders immediately** via phone and email.
3. **Execute the emergency maintenance.**
4. **Document what was done** and why it couldn't wait.
5. **Conduct a post-maintenance review** within 24 hours.

### Maintenance Blackout Periods

Avoid scheduling maintenance during:

| Period | Reason |
|--------|--------|
| Business hours (09:00-17:00 local) | User impact |
| End-of-month processing | Financial processing |
| Major company events | Business operations |
| Holiday periods | Staff availability |

---

## Maintenance Documentation

All maintenance activities must be documented. Use the following template:

### Maintenance Record

| Field | Description |
|-------|-------------|
| **Maintenance ID** | Unique identifier |
| **Type** | Scheduled, emergency, or change request |
| **Description** | What was done |
| **Schedule** | When it was performed |
| **Duration** | Actual time taken |
| **Impact** | Services affected, if any |
| **Result** | Success, partial success, or failure |
| **Issues** | Any problems encountered |
| **Rollback** | Whether rollback was needed and what was done |
| **Performed by** | Operator(s) who performed the maintenance |
| **Verified by** | Operator(s) who verified the result |

### Maintenance Log Location

All maintenance records are stored in the audit trail and can be accessed via:

**API Endpoint:** `GET /api/v1/automations/audit?eventType=maintenance`

**Via Dashboard:**
1. Navigate to Automation > Audit Trail.
2. Filter by event type "maintenance".
3. Browse the maintenance history.
