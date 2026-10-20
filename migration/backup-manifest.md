# Backup Manifest — Mission Control Migration

**Status:** design for approval. **No backup has been taken yet.** Producing the first backup is a
Phase 4 action behind its own approval gate.
**Labels:** **[V]** verified · **[A]** assumption · **[?]** unresolved · **[R]** recommendation.

---

## 1. Why this document exists

There are **no backups of any kind** on the source host: no `pg_dump` artefacts, no `archive_mode`
(`archive_mode=off`), no PITR, no snapshot policy recorded in the repo. `scripts/backup-db.ps1` and
`docs/administrator/BACKUP_AND_RESTORE.md` exist but were never run against this database **[V]**.

A migration that overwrites a destination volume without a verified source backup is unrecoverable.
Therefore: **no destination write happens before the manifest items in §3 are produced, hashed and
restore-tested** (Phase 4 gate).

---

## 2. Backup scope and sizes

| # | Item | Source path / object | Size | Method | Why |
|---|---|---|---|---|---|
| B1 | PostgreSQL logical dump | container `missioncontrol-postgres-1`, DB `mission_control` | **439 MB logical** (502 MB on disk) [V] | `pg_dump -Fc` (16.14, in-container) | application state |
| B2 | Repo working tree | `/opt/MissionControl` | 553 MB (backend 233 MB, frontend 277 MB) [V] | `tar` excluding `node_modules`, `dist`, `.git` + `git bundle` | backend runs from this tree |
| B3 | Untracked env/secrets | `/opt/MissionControl/.env` | < 2 KB | `scp`/`tar` over SSH, mode 600 | DB + Fernet key |
| B4 | TLS material | `/etc/letsencrypt` (root 0700/0600) | ~ 12 KB live dirs + archive | `tar` as root | edge certificates |
| B5 | Live uncommitted config | `docker-compose.yml`, `nginx/default.conf` | 2 files | **already preserved** in branch `migration/prod-live-snapshot-2026-10-20` (`75a8280`) | provenance |
| B6 | Redis data | volume `missioncontrol_redis_data` | 20 KB, **0 keys** [V] | **not backed up** (recreate empty) | nothing to lose |
| B7 | Dockhand state | volume `missioncontrol_dockhand_data` | 956 KB | not migrated; optional snapshot in B9 | D-B: not part of the target |
| B8 | Host edge-agent state | `/var/lib/mission-control-agent/edge.db` | 272 MB | **not migrated** (D-C) | retires with the source host |
| B9 | Full source snapshot (optional) | `/opt/MissionControl` + volumes | ~ 2 GB | `tar`/`docker run … tar` | belt-and-braces before decommission |

`agent_commands` is inside B1; see §4.

---

## 3. Storage, naming, retention

| Copy | Location | Format | Retention |
|---|---|---|---|
| Primary | BE VM `/var/backups/missioncontrol/` (mode 700) | `mc-<UTC timestamp>-<git sha>.dump` | 7 daily |
| Secondary (off-host) | operator workstation `C:\Backups\MissionControl\` via `scp` | same files | 4 weekly |
| Optional tertiary | encrypted archive in cloud storage | 7-Zip AES-256 or `gpg -c` | 3 monthly |

Rules:

- Every artefact gets a sibling `.sha256` and a `MANIFEST.txt` line (file, size, sha256, source git SHA,
  UTC time, operator).
- **B3 and B4 are secrets.** They are never stored unencrypted in a synced folder (OneDrive/Dropbox) and
  never committed. If the off-host copy includes them, it must be an encrypted archive; the passphrase is
  held outside the repository. **[?] U6**
- Restore-test evidence is appended to `execution-log.md` before any destination restore.
- A backup is not counted as valid until its restore test passes (§5).

**Targets:** RPO 24 h (nightly) → 0 during the cutover window because a fresh dump is taken inside it;
RTO ≈ 1 h (dump + restore + start) on the destination.

---

## 4. `agent_commands` — preservation profile (D-D)

Decision: **migrate the complete dataset; no pruning in this migration.**

| Property | Value [V] |
|---|---|
| Table size | **420 MB total** of a 439 MB database |
| Breakdown | heap 64 MB, indexes 8.9 MB, remainder ≈ 347 MB **TOAST** (large result payloads) |
| Rows | **≈ 98,000** (98,015 at audit time) |
| Average row | ≈ 4.5 KB |
| Status mix | completed 64,450 · failed 33,564 · dispatched 1 |
| Distribution | heavily skewed: the busiest agent holds ~31 k rows; the host agent (id 3) has only **2 rows**, last on 2026-09-22 |
| Growth | 2.6 k–5.4 k rows/day ≈ 7–26 MB/day of row data over the last 10 days |
| Relationships | **no foreign keys reference it**; it is a leaf/audit table |
| Write pattern | continuous inserts from agent polling; ~5–15 s per agent across ~15 agents |
| Restore implications | large TOAST means restore time is dominated by 98 k row inserts; single-threaded `pg_restore` is acceptable |

Estimates:

| Step | Estimate | Basis |
|---|---|---|
| Dump | 30–90 s | 439 MB logical, TOAST compresses well |
| Dump file size | 100–200 MB [A] | `-Fc` zlib over repetitive JSON |
| Transfer FE/BE ↔ workstation at 0.5 Gbps | 20–40 s [A] | 100–200 MB |
| Transfer source → BE over the internet | 1–3 min [A] | source egress limited, unmeasured |
| Restore on BE | 2–5 min [A] | 98 k rows, 1 vCPU, 956 MB RAM |
| Scratch-DB restore test | 5–10 min [A] | includes verification queries |

Destination capacity check: dump + restored DB + WAL ≈ 1 GB against **42 GB free** [V] — ample.

**Retention policy:** deliberately **out of scope**. It needs the data's purpose (agent diagnostics vs.
audit evidence), an agreed window, and a legal/operational review. Recommended follow-up: propose a
90-day window with a monthly aggregate after cutover is stable. No `DELETE`/`TRUNCATE`/`VACUUM FULL` on
production as part of this migration.

---

## 5. Restore procedure (BE, scratch database first)

```bash
# 0. preconditions: postgres container healthy, 1 GB free disk, dump hash verified
sha256sum -c mc-<ts>-<sha>.dump.sha256

# 1. create a scratch database for the test
docker exec mc-postgres psql -U mission_control -d postgres -c \
  "CREATE DATABASE mission_control_restore_test;"

# 2. restore into the scratch DB (no --clean, no owner changes)
docker exec -i mc-postgres pg_restore -U mission_control \
  -d mission_control_restore_test --no-owner --no-privileges --exit-on-error \
  < /var/backups/missioncontrol/mc-<ts>-<sha>.dump

# 3. verify (see §5.1), then drop the scratch DB
docker exec mc-postgres psql -U mission_control -d postgres -c \
  "DROP DATABASE mission_control_restore_test;"
```

Production restore (cutover) uses the same command into the real `mission_control` database on a **fresh,
empty volume**, after which the backend starts.

### 5.1 Verification criteria (all must pass)

| Check | Expected |
|---|---|
| Table count | 78 (same as source) |
| Alembic head | `h7h8h9i1j2k3` |
| `agent_commands` row count | equal to source count at dump time (±0, no live writes) |
| Top tables (`agents`, `integration_profiles`, `agent_remote_targets`, `veeam_backup_servers`) | row counts equal |
| Fernet decrypt | one stored credential decrypts with the copied `MISSIONCONTROL_SECRET_KEY` (prints only "OK") |
| Sequences | backend insert succeeds without PK collision (smoke insert/rollback) |
| Restore log | no `ERROR` lines (warnings about extensions/owners acceptable) |
| API | `/api/v1/health/ready` 200, `/api/v1/version` = `3.0.0-rc1` |

**Non-obvious risk:** the MISSIONCONTROL_SECRET_KEY is stored *outside* the dump. A restore into a host
with a different key succeeds but every encrypted integration credential fails silently at first use.
The key is therefore backed up (B3) and hash-compared before restore.

---

## 6. Backup schedule (design)

| When | What | Where | Who |
|---|---|---|---|
| Daily 02:30 UTC | B1 `pg_dump -Fc` + sha256 | BE `/var/backups/missioncontrol` | systemd timer `mc-backup.timer` |
| Weekly Sun 03:00 UTC | pull latest dumps + B2 + B3 + B4 | operator workstation (encrypted archive) | manual/scripted |
| Before cutover | B1 fresh + B1–B5 complete set | both locations | operator (Phase 4 gate) |
| Before decommission | B9 full snapshot | off-host | operator (Phase 8, separate approval) |

Timer unit (Phase 4, not created now):

```ini
# /etc/systemd/system/mc-backup.service
[Service]
Type=oneshot
ExecStart=/usr/local/bin/mc-backup.sh
# /etc/systemd/system/mc-backup.timer
[Timer]
OnCalendar=*-*-* 02:30:00 UTC
Persistent=true
```

`mc-backup.sh` uses `set -euo pipefail`, writes to a temp file, verifies `pg_restore --list` succeeds,
then atomically renames and rotates. Failure is surfaced via `systemctl status` and (optionally) an
alert email — no alerting exists today, so **failure detection is manual** unless the owner asks for it.

---

## 7. What is explicitly NOT in scope

- WAL archiving / PITR (`archive_mode=off` today). Recommended as a post-migration change; needs a
  separate approval because it changes `postgresql.conf` and disk growth.
- Off-site replication to a third region.
- Backing up container logs, images, or test fixtures.
- Backing up the host edge-agent DB (272 MB, retires with the host) and Dockhand state (retained on the
  source host, which is not decommissioned).
