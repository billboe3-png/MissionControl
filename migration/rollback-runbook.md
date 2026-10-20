# Rollback Runbook — Mission Control 2-VM Migration

**Status:** design for approval. **Not executed.**
**Guiding rule:** the source host is **not decommissioned** and remains authoritative until the migration
is declared closed. Rollback is therefore a *routing* change plus a *data reconciliation* step, not a
rebuild.

Rollback authority: the owner (or the nominated operator during the window). Any single failed check in
`cutover-runbook.md` §4 is sufficient to trigger rollback without further debate.

---

## 1. Rollback scenarios

| ID | Scenario | Rollback needed | Data risk |
|---|---|---|---|
| R1 | Failure **before** the source backend is stopped | no action / start source backend | none |
| R2 | Failure **after** source stop but **before** DNS switch | start source backend, discard BE work | **none** (source DB untouched — the dump is read-only) |
| R3 | Failure **after** DNS switch, BE has accepted writes | DNS back + start source backend + reconcile | **yes** — writes accepted on BE after the switch |
| R4 | Failure after 24 h (post-migration defect, not cutover) | **not a rollback** — forward-fix on the destination | — |
| R5 | Destination host loss before cutover | none (source still live) | none |
| R6 | Destination host loss after cutover | forward recovery: rebuild BE from the latest dump | up to 24 h (RPO) |

**Key property of the design:** because the source is only *stopped* and never modified, R2 is always
lossless. The entire risk window is R3, bounded by the time between DNS switch and the rollback decision.

---

## 2. R2 — rollback before DNS (target ≤ 5 minutes)

```bash
[SRC] docker start missioncontrol-backend-1
[SRC] docker ps --filter name=missioncontrol-backend-1 --format '{{.Status}}'
[SRC] curl -fsS http://127.0.0.1:8000/api/v1/health/ready      # via nginx or localhost publish
```

Then:

1. Confirm nginx on the source still proxies to its local backend (no config was changed on the source).
2. Verify externally: `curl -I https://missioncontrol.optichosting.co.za/` → 200 (DNS still points at the
   source).
3. Stop the destination stacks (they hold restored copies, not authoritative data):
   ```bash
   [BE] docker compose -f docker-compose.backend.yml stop
   [FE] docker compose -f docker-compose.frontend.yml stop
   ```
4. Record the abort reason and the stage reached in `execution-log.md`.
5. **Do not** delete the BE database volume — it is evidence for the fix.

---

## 3. R3 — rollback after DNS switch

### 3.1 Immediate (first 5 minutes)

1. **DNS back** to `34.35.177.209` (TTL already 60 s from the pre-cutover step).
2. Start the source backend:
   ```bash
   [SRC] docker start missioncontrol-backend-1
   ```
3. Verify from three external resolvers and via HTTPS:
   ```bash
   dig +short @1.1.1.1 missioncontrol.optichosting.co.za
   curl -fsS -o /dev/null -w '%{http_code}\n' https://missioncontrol.optichosting.co.za/api/v1/health/ready
   ```
4. Confirm agents return to `online` on the source (≤ 60 s).
5. Leave BE running but **do not** accept traffic to it: stop the FE nginx stack so a stale DNS cache cannot
   reach it:
   ```bash
   [FE] docker compose -f docker-compose.frontend.yml stop nginx
   ```

### 3.2 Data reconciliation (bounded, explicit)

Writes accepted by BE after the switch are the only data at risk. They are identified by time:

1. Take an immediate dump of the BE database:
   ```bash
   [BE] docker exec mc-postgres pg_dump -U mission_control -Fc mission_control \
          > /var/backups/missioncontrol/mc-rollback-$(date -u +%Y%m%dT%H%M%SZ).dump
   ```
2. Identify tables with rows newer than the switch time (`created_at`/`updated_at`), typically:
   `agent_commands` (agent results), `agents` (heartbeats/inventory), `audit_logs`, integration tables.
3. Decide per table:
   - **Regenerable telemetry** (heartbeats, inventory, command results that agents will re-send) → discard.
   - **Human/configuration changes made in the window** (integration edits, settings) → re-apply manually
     on the source, using the BE dump as the reference.
4. Record every decision in `execution-log.md`. **Never** copy the whole BE database over the source DB.

### 3.3 Close-out

- Keep the BE dump for 7 days.
- Revert any destination-only configuration (none is expected — the source config was not modified).
- Schedule a post-mortem; the next attempt starts from the failure point, not from zero.

---

## 4. R4 — post-cutover defect (no rollback)

After the 7-day rollback window, the source host is stale by definition. Attempting to "roll back" would
lose days of data. The correct action is a **forward fix**:

1. Identify the defect; patch on `migration/2vm-deploy`.
2. Rebuild the affected image off-host, load, restart the single service.
3. If the DB is affected, restore the **latest nightly dump** into a scratch DB to reproduce, never into
   production.

Rollback after 7 days requires a new, explicitly approved plan with a data-reconciliation design.

---

## 5. Point-of-no-return

| Event | Consequence |
|---|---|
| Source backend stopped | reversible (start it) |
| BE restored + started | reversible |
| DNS switched | reversible within minutes **if** BE writes are reconciled |
| 7 days elapsed / source host decommissioned | **irreversible** — requires the new plan |

The source host is **not** to be deleted, downgraded, or repurposed as part of this migration. Its
decommissioning is a separate phase with its own approval and its own final backup (B9).

---

## 6. Rollback validation checklist

| # | Check | Pass criterion |
|---|---|---|
| 1 | DNS | all three resolvers return `34.35.177.209` |
| 2 | Source API | `/api/v1/health/ready` 200 |
| 3 | UI | login + dashboard load over HTTPS |
| 4 | Agents | online count returns to the pre-cutover baseline |
| 5 | Plugins | one full sync cycle succeeds for each installed plugin |
| 6 | FE nginx | stopped (cannot serve stale traffic) |
| 7 | Data | reconciliation table in §3.2 completed and signed off |
| 8 | Logs | abort reason, timings and decisions recorded |

---

## 7. Time targets

| Stage | Target | Hard limit before escalation |
|---|---|---|
| R2 (pre-DNS) | 5 min | 15 min |
| R3 DNS reversion | 5 min | 15 min |
| R3 reconciliation | 30 min | 2 h (then declare data impact) |
| Full service restored | 10 min | 30 min |

If the hard limit is reached, the owner decides between continuing reconciliation and accepting the
documented data loss with a follow-up replay.
