# Destination preparation — Mission Control 2-VM migration (Phase 3)

**Status:** Phase 3 executed for host preparation only. No production data was migrated, no backup was
created, DNS was not changed, and the source server was not modified except for the separately approved
D-F routing change.

**Labels:** **[V]** verified by command · **[A]** assumption · **[?]** unresolved.

---

## 1. Verified destination baseline (before Phase 3)

Both VMs, measured 2026-10-20:

| Item | FE `10.0.0.26` / `84.12.77.251` | BE `10.0.0.33` / `84.12.82.239` |
|---|---|---|
| OCI display name | `Mission-Control-Frontend` | `Mission-Control-Backend` |
| Shape / region | `VM.Standard.E2.1.Micro`, `af-johannesburg-1` | same |
| OS / kernel | Ubuntu 22.04.5 LTS, `6.8.0-1062-oracle` | same |
| RAM | 956 MB total, 643 MB available, **no swap** | 956 MB total, 634 MB available, **no swap** |
| Disk | 45 GB, 42 GB free (7 % used) | same |
| Docker / git / rsync / certbot / fail2ban | all **absent** | all **absent** |
| `python3` | 3.10.12 (no pip) | 3.10.12 (no pip) |
| Listeners | sshd 22, rpcbind **111**, resolved stub 53 | same |
| Host firewall | persisted iptables: allow 22 (**any source**), REJECT everything else | identical |
| `ip_forward` | 0 | 0 |
| Egress (docker.io, github, ubuntu mirrors) | reachable | reachable |
| Public IP reservation | **reserved** (owner-confirmed, U1) | reserved |

---

## 2. Firewall design and the discrepancy found (U2)

The stock OCI image firewall accepts **port 22 from any source**. Only the cloud security list restricted
SSH. Phase 3 narrows the host rule to the administrator range, which is a *tightening*, consistent with
U2's instruction not to broaden rules.

`ADMIN_CIDR` used: `45.220.11.50/32` (home) and `168.253.204.10/32` (work) — matching the cloud rules
supplied by the owner.

**Cloud-side discrepancy (report as requested):** the supplied ingress list contains no
`10.0.0.26/32 → 8000` rule; port 8000 is permitted by the broad `10.0.0.0/16` all-protocols rule. So
"BE 8000 from the FE VM only" is enforced by **container bind address + host firewall**, not by the cloud.
It is not internet-reachable (measured), but it is reachable from any host in the VCN.

---

## 3. Capacity assessment (D-A) — measured, not assumed

| Role | Measured production usage | Destination headroom |
|---|---|---|
| Backend VM (backend + postgres + redis) | 175 + 47 + 4 = **226 MB** | 956 MB − 226 MB − dockerd (~80–120 MB) ≈ 600 MB free |
| Frontend VM (nginx + frontend) | 5 + 3 = **8 MB** | ~800 MB free |
| Risk peak | `pg_restore` of a 439 MB database, Vite build | mitigated by off-host builds and a swap safety net |

**Recommendation:** 2 GB swap as a safety net only (`vm.swappiness=10`), no resizing yet, off-host builds.
Resize triggers: sustained host RAM > 80 %, any OOM kill, or sustained swap thrash.

---

## 4. Deployment layout

| Host | Path | Content |
|---|---|---|
| both | `/opt/missioncontrol/` | deployed working tree (compose files + code) |
| FE | `/opt/missioncontrol/deploy/migration-2vm/nginx/default.conf` | edge config |
| FE | `/etc/letsencrypt/` | TLS material (copied, root-only) |
| FE | `/var/www/letsencrypt/` | ACME webroot |
| BE | `/opt/missioncontrol/.env` | secrets, mode 600 |

---

## 5. Remaining blockers before data migration

1. **Backup and recovery plan not yet approved** (U6). No backup is created in Phase 3 by instruction.
2. **`.env` value transfer** requires the production Fernet key and DB password; must be moved over SSH
   with mode 600 and verified by hash.
3. **OCI NSG question** unresolved: whether an NSG applies in addition to the security list cannot be read
   from inside the guest.
4. **Image transfer** not yet executed (built and digested on the workstation; see `build-and-transfer.md`).
