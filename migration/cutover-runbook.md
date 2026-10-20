# Cutover Runbook — Mission Control 2-VM Migration

**Status:** design for approval. **Nothing here has been executed.**
**Owner approval gates:** Phase 4 (first backup), Phase 5 (destination data install), Phase 7 (DNS /
production switch). Cutover itself requires an explicit go decision recorded in `execution-log.md`.

Legend: `[SRC]` production `34.35.177.209` · `[FE]` `84.12.77.251` / `10.0.0.26` ·
`[BE]` `84.12.82.239` / `10.0.0.33` · `[WS]` operator workstation (Docker 29.8.2, 8.1 GB).

---

## 1. Preconditions (all must be true before T-0)

| # | Condition | Evidence required |
|---|---|---|
| P1 | Phase 3 complete: Docker, swap, firewall, directories on FE/BE | `installation-report` entries in `execution-log.md` |
| P2 | Phase 4 complete: full backup set B1–B5 taken, hashed, **restore-tested** | `backup-manifest.md` §5 checklist passed |
| P3 | Images built off-host and loaded on FE/BE with recorded tags/digests | `docker images --digests` output |
| P4 | BE stack runs for ≥ 24 h with restored data; all health checks green | screenshot/log excerpt |
| P5 | FE stack validated with `curl --resolve` against the FE private/public IP; TLS served from the copied cert | command output |
| P6 | DNS TTL lowered to 60 s ≥ 24 h before cutover | `dig` TTL check |
| P7 | `/dockhand/` decision applied or explicitly deferred (D-F) | owner statement |
| P8 | OCI reserved-IP question resolved (U1) and ingress rules confirmed (U2) | console evidence |
| P9 | Rollback runbook rehearsed (at least table-top); source host untouched and startable | `rollback-runbook.md` |
| P10 | Change window announced; agents/site users informed | comms record |

---

## 2. Timeline

| When | Action | Host |
|---|---|---|
| T-7 d | Lower DNS A-record TTL to 60 s (**separate approval**) | registrar |
| T-3 d | Build images on `[WS]`; `docker save`/`load` to FE and BE; record digests | WS → FE/BE |
| T-2 d | Install Docker/swap/firewall; copy TLS; copy working tree + `.env`; start BE stack with a **restore-tested** dump; 24 h soak | FE/BE |
| T-1 d | Full backup set; final dry run of validation script; confirm rollback assets | SRC/WS |
| T-0 | **Cutover window** (§3) | all |
| T+0 h | Post-switch monitoring (§5) | — |
| T+24 h | Keep source host stopped-but-intact; decide on decommission (separate phase) | SRC |

---

## 3. Cutover window (target: ≤ 20 minutes user-visible)

### 3.1 T-0:00 — announce and freeze

1. Announce start in the change channel.
2. Stop **writes** by stopping the source API:
   ```bash
   [SRC] docker stop missioncontrol-backend-1     # nginx stays up → 502 for API calls
   ```
3. Confirm no backend process remains and record the exact row counts that must be reproduced:
   ```sql
   [SRC] select count(*) from agent_commands;            -- expect ≈98k
   [SRC] select count(*) from agents;
   [SRC] select count(*) from integration_profiles;
   [SRC] select version_num from alembic_version;        -- h7h8h9i1j2k3
   ```
4. Freeze filesystem writers that are not the DB (none expected — no uploads, `backend/app/data` empty).

> Agents continue polling and receive 502/timeouts. Their client retries and buffers locally; this is
> the same failure mode as the 2026-10-20 OOM event and is expected.

### 3.2 T-0:02 — final dump

```bash
[SRC] TS=$(date -u +%Y%m%dT%H%M%SZ)
[SRC] docker exec missioncontrol-postgres-1 pg_dump -U mission_control -Fc mission_control \
        > /tmp/mc-$TS-final.dump
[SRC] sha256sum /tmp/mc-$TS-final.dump | tee /tmp/mc-$TS-final.dump.sha256
```

### 3.3 T-0:04 — transfer and restore

```bash
# source → workstation (staging, keeps a copy off-host)
[WS] scp billboe3@34.35.177.209:/tmp/mc-$TS-final.dump* .
# workstation → BE
[WS] scp mc-$TS-final.dump* ubuntu@84.12.82.239:/var/backups/missioncontrol/
[BE] sha256sum -c /var/backups/missioncontrol/mc-$TS-final.dump.sha256

# BE: ensure the target DB is empty (fresh volume) then restore
[BE] docker compose -f docker-compose.backend.yml stop backend
[BE] docker exec mc-postgres psql -U mission_control -d postgres \
       -c "DROP DATABASE IF EXISTS mission_control;" \
       -c "CREATE DATABASE mission_control OWNER mission_control;"
[BE] docker exec -i mc-postgres pg_restore -U mission_control -d mission_control \
       --no-owner --no-privileges --exit-on-error \
       < /var/backups/missioncontrol/mc-$TS-final.dump
```

> Alternative (faster, less downtime): restore into `mission_control_final` and, at the switch, rename
> databases. Only use if P4 proved the same sequence works; it removes the drop/recreate step from the
> critical path.

### 3.4 T-0:08 — start and verify the backend

```bash
[BE] docker compose -f docker-compose.backend.yml up -d
[BE] docker compose -f docker-compose.backend.yml ps
[BE] curl -fsS http://127.0.0.1:8000/api/v1/health/live
[BE] curl -fsS http://127.0.0.1:8000/api/v1/health/ready
[BE] curl -fsS http://127.0.0.1:8000/api/v1/version     # expect 3.0.0-rc1
[BE] docker logs --tail 200 mc-backend | grep -iE 'error|exception|traceback'   # expect none unexpected
```

Run the §4 verification set **locally on BE** before touching DNS. If any check fails → **ABORT**
(§6) and follow `rollback-runbook.md`.

### 3.5 T-0:10 — verify the edge (pre-DNS)

```bash
[WS] curl -k --resolve missioncontrol.optichosting.co.za:443:84.12.77.251 \
       -o /dev/null -w '%{http_code}\n' https://missioncontrol.optichosting.co.za/
[WS] curl -k --resolve missioncontrol.optichosting.co.za:443:84.12.77.251 \
       https://missioncontrol.optichosting.co.za/api/v1/health/ready
```

Checks: 200, valid cert chain for the hostname, login page loads, websocket connects, `/dockhand/`
returns **404** (post D-F design), static assets load.

### 3.6 T-0:12 — DNS switch

1. Change the A record `missioncontrol.optichosting.co.za` → `84.12.77.251` (TTL 60 s).
2. Verify from **three external resolvers** (the Windows workstation is unreliable for destination
   reachability):
   ```bash
   dig +short @1.1.1.1  missioncontrol.optichosting.co.za
   dig +short @8.8.8.8  missioncontrol.optichosting.co.za
   dig +short @9.9.9.9  missioncontrol.optichosting.co.za
   ```
3. Confirm HTTPS 200 and API 200 through DNS.

### 3.7 T-0:15 — fleet and application acceptance

| Check | Expected |
|---|---|
| `/api/v1/agents` | agents transition back to `online` within ~2 polling cycles (≤ 60 s) |
| Agent command flow | new rows appear in `agent_commands`; no 401/5xx storm in backend logs |
| Dashboards | Docker, System Info, Veeam, Zabbix, UniFi, MikroTik, D-Link, Git, Hyper-V widgets render |
| Encrypted credentials | one Veeam/Zabbix integration performs a real API call (proves Fernet key) |
| Login + session | valid login, page reload stays authenticated |
| Websocket | live updates resume |
| TLS | `openssl s_client -connect …:443 -servername …` → correct CN/expiry |
| Public surface | 80 → 301, 443 only; `3000`, `8000`, `5432`, `6379` closed from outside |

### 3.8 T-0:20 — unfreeze

1. Do **not** restart the source backend. Leave it stopped.
2. Record the completed window and all verification output in `execution-log.md`.
3. Keep the source host powered off-service but intact for **≥ 7 days** (rollback window).

---

## 4. Verification set (single script, run at each stage)

1. `docker compose ps` — all services `running`, health `healthy`.
2. `/api/v1/health/live` → 200, `/api/v1/health/ready` → 200.
3. `/api/v1/version` → `3.0.0-rc1`.
4. DB: table count 78, `alembic_version` = `h7h8h9i1j2k3`, `agent_commands` count == pre-cutover count.
5. Decrypt test: one encrypted credential resolves (no plaintext printed).
6. Auth: login succeeds; an invalid login is rejected.
7. Plugins: each installed plugin reports loaded; background loops log a successful cycle within 5 min.
8. Edge: HTTPS 200, cert dates, HSTS/headers unchanged from baseline.
9. Logs: no new tracebacks in 10 min; no OOM kills (`dmesg | grep -i oom`).
10. Resource: host RAM < 80 %, swap usage < 50 % of 2 GB, disk free > 30 GB.

---

## 5. Post-switch monitoring (T+0 → T+24 h)

| Interval | Watch |
|---|---|
| 15 min | health endpoints, backend error rate, agent online count, host RAM/swap/disk |
| 1 h | DB size growth, `agent_commands` inserts, plugin sync results, TLS, nginx 5xx |
| 4 h | OOM kills, docker restarts, backup timer (first scheduled run) |
| 24 h | full dashboard spot-check with the owner; capacity decision input (D-A trigger conditions) |

Trigger conditions for resizing (D-A): sustained host RAM > 80 %, any OOM kill, sustained swap
thrash, or backup duration degrading.

---

## 6. Abort points

| Point | Abort if | Action |
|---|---|---|
| After dump | dump hash mismatch, `pg_restore --list` fails | restart source backend (`docker start missioncontrol-backend-1`); no data changed yet |
| After restore | table count / alembic head / row counts wrong | keep source stopped, fix BE, retry restore; if > 20 min, roll back |
| After BE start | readiness fails, plugins crash, decrypt fails | roll back (source untouched) |
| After DNS | errors only visible through the edge, agents not returning, auth broken | roll back DNS first, then source backend |

---

## 7. Communications

- Pre-window: "Mission Control will be briefly unavailable at <time> (≤ 20 min)."
- In-window: single status line at each stage (freeze / restore / verify / DNS / done).
- Post-window: confirmation + what changed (host moved, same URL and credentials).
- On rollback: "Service restored on the previous host; no data loss expected" — unless §4 in the rollback
  runbook says otherwise.
