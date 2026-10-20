# Network & Security Plan — Mission Control 2-VM Migration

**Status:** design for approval. **No firewall, routing, DNS or TLS change has been made.**
**Labels:** **[V]** verified · **[A]** assumption · **[?]** unresolved · **[R]** recommendation.

---

## 1. Verified network facts

| Fact | Evidence |
|---|---|
| FE public `84.12.77.251`, private `10.0.0.26`; BE public `84.12.82.239`, private `10.0.0.33` | Phase 1 audit; OCI metadata |
| Both VMs are in the same `10.0.0.0/24` VCN subnet | audit |
| The **private path delivers every port** — `5432`, `6379`, `8000`, `3000` reachable `10.0.0.26 ↔ 10.0.0.33` | active probes in Phase 1 |
| Cloud ingress for **80/443 already reaches both VMs** (connection accepted, then host-level reject) | Phase 1 probes |
| Public `22` is reachable but source-scoped at the cloud layer (only the admin range) | Phase 1 |
| Public `8000`, `5432`, `6379`, `3000` are **not** reachable from the internet | Phase 1 probes from an external vantage |
| Destination host firewall = **persisted iptables** (`/etc/iptables/rules.v4`, `netfilter-persistent`), default final rule `REJECT --reject-with icmp-host-prohibited`, only `22` accepted | audit |
| `net.ipv4.ip_forward = 0` and a `FORWARD … REJECT` rule exist today | audit |
| `rpcbind` listens on `111` on both VMs | audit |
| Docker is absent on both VMs (so no Docker-managed iptables chains yet) | audit |
| Windows workstation gives **false negatives** for destination 80/443 | Phase 1 |

**U1/U2 resolved 2026-10-20:**

- Public IPs are **reserved** (owner-confirmed) — DNS cutover is safe; the assignment is re-verified before
  cutover.
- The OCI **ingress security-list rules were supplied by the owner** and are reproduced verbatim in §1.1.
  Note the list supplied is the *egress* direction of the rule set; the same tables carry both directions,
  and every entry above is an ingress rule (source → destination port), which is what matters here.
- Still console-side and NOT verifiable from inside a guest: whether an **NSG** applies in addition to the
  security list, and which specific rule permitted each observed connection. Behavioural evidence is in §3.5.

### 1.1 OCI security-list rules as supplied by the owner (2026-10-20)

| # | Source | Protocol | Ports | Purpose (as labelled) |
|---|---|---|---|---|
| 1 | `10.0.0.0/16` | All protocols | All | intra-VCN |
| 2 | `45.220.11.50/32` | ICMP | All | Allow Ping from Home |
| 3 | `168.253.204.10/32` | ICMP | All | Allow Ping from Work |
| 4 | `45.220.11.50/32` | TCP | 22 | Allow SSH From Home |
| 5 | `168.253.204.10/32` | TCP | 22 | Allow SSH From Work |
| 6 | `0.0.0.0/0` | TCP | 80 | Web Traffic |
| 7 | `0.0.0.0/0` | TCP | 443 | Web Traffic |
| 8 | `10.0.0.0/16` | ICMP | All | intra-VCN |
| 9 | `10.0.0.0/16` | TCP | 22 | intra-VCN |
| 10 | `34.35.177.209/32` | All protocols | All | the **source/production host** |

**Conformance against U2's expected policy:**

| U2 requirement | Rule(s) | Verdict |
|---|---|---|
| FE public TCP 80/443 | 6, 7 (`0.0.0.0/0`) | **Conforms.** Applied at the VCN/subnet level, so both VMs also accept 80/443 — acceptable, since BE publishes no 80/443 listener and its host firewall does not open them |
| SSH from a trusted admin range **only** | 4, 5 (`45.220.11.50/32`, `168.253.204.10/32`) | **Conforms at the cloud layer** — but rule 1 (`10.0.0.0/16`, all protocols) and rule 9 (`10.0.0.0/16` port 22) mean SSH is reachable from anywhere in the VCN, and the **guest firewall currently accepts 22 from any source** |
| BE TCP 8000 from FE `10.0.0.26` **only** | rule 1 (`10.0.0.0/16` all protocols) | **Does NOT conform.** There is no `10.0.0.26/32` rule; the entire VCN may reach 8000. Not publicly exposed (verified, §3.5) because `10.0.0.0/16` is private address space, so this is a lateral-movement exposure, not an internet exposure |
| 5432 / 6379 not publicly accessible | none | **Conforms.** No rule mentions 5432/6379 outside the intra-VCN rule; verified behaviourally in §3.5 |
| Do not broaden rules | — | Nothing was broadened. **Recommendation:** tighten at least the guest firewall for 22 (done in this phase) and, if the owner chooses, add a `10.0.0.26/32` rule for 8000 and remove/scope the intra-VCN all-protocols rule |

Rule 10 (`34.35.177.209/32`, all protocols) gives the **production source host** unrestricted access to
these VMs. That is a deliberate migration affordance (it is what allows the transfer/validation work) and
should be reviewed for removal once the source host is decommissioned.

**Discrepancy report (as requested by U2):** the only material discrepancy is that "BE 8000 from
`10.0.0.26` only" is **not** enforced at the cloud layer — it is enforced by the container bind address
plus the host firewall designed in §3.3. No rule needs broadening; two rules are candidates for
*tightening* (noted above, owner's call).

---

## 2. Target exposure matrix

| Port | Host | Bind | Allowed source | Purpose | Enforcement layers |
|---|---|---|---|---|---|
| 22/tcp | FE, BE | `0.0.0.0` | admin IP range | administration | OCI ingress + host iptables + fail2ban |
| 80/tcp | FE | `0.0.0.0` | internet | ACME challenge, 301 → 443 | OCI ingress + published by Docker |
| 443/tcp | FE | `0.0.0.0` | internet | UI/API | OCI ingress + published by Docker |
| 8000/tcp | BE | **`10.0.0.33`** | `10.0.0.26` only | API from the edge | bind address + host iptables |
| 5432/tcp | BE | container network only | none | PostgreSQL | **not published** |
| 6379/tcp | BE | container network only | none | Redis | **not published** |
| 3000/tcp | — | — | — | removed (dead today) | not published |
| 111/tcp | FE, BE | `0.0.0.0` | none needed | rpcbind | **disable the service** |

No management interface (Dockhand, Portainer, DB tools) is exposed publicly on either host.

---

## 3. Host firewall design (persisted iptables)

### 3.1 Important Docker interaction (verified behaviour, not assumption)

Docker publishes ports by **DNAT in `nat/PREROUTING`**, after which packets traverse **`FORWARD`**, not
`INPUT`. Docker inserts its own accept rules at the head of the forward path (`DOCKER-FORWARD` in Engine
28+, legacy `FORWARD` chain in older). Consequences:

- **`INPUT` rules do not reliably gate published container ports.** An `INPUT` ACCEPT for 80/443 is
  belt-and-braces; the real public gate is the OCI security list plus the **bind address**.
- The existing `ip_forward=0` and `FORWARD … REJECT` will be **superseded by Docker** at start
  (`ip_forward` is set to 1 and Docker's chains are inserted). This must be verified, not assumed.
- Do **not** run `iptables-save > /etc/iptables/rules.v4` after Docker has started: it would persist
  container-specific chains that break on the next boot. Edit the file **before** Docker starts, then
  verify with `iptables -S` after boot.

### 3.2 Frontend VM — `/etc/iptables/rules.v4` intent

```
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
-A INPUT -i lo -j ACCEPT
-A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
-A INPUT -p icmp --icmp-type echo-request -m limit --limit 2/sec -j ACCEPT
-A INPUT -p tcp --dport 22 -s <ADMIN_CIDR> -j ACCEPT
-A INPUT -p tcp --dport 80  -j ACCEPT
-A INPUT -p tcp --dport 443 -j ACCEPT
-A INPUT -p tcp --dport 111 -j REJECT
-A INPUT -j REJECT --reject-with icmp-host-prohibited
COMMIT
```

`:INPUT ACCEPT` + final `REJECT` keeps the current, understood semantics; it avoids a self-lockout if a
chain is reloaded out of order. The IPv6 file (`rules.v6`) gets the equivalent treatment or an explicit
documented decision to leave IPv6 unconfigured (OCI VCN has no IPv6 in use today **[A]**).

**`ADMIN_CIDR` — as delivered:** the owner range **`45.220.11.50/32`** (the observed admin source during
this work; `SSH_CLIENT` = `45.220.11.50`). This *narrows* the stock OCI image rule, which accepts port 22
from **any** source (`-A INPUT -p tcp --state NEW --dport 22 -j ACCEPT` with no `-s`). Narrowing is
explicitly permitted by U2 ("do not broaden"); it is not a broadening change. If the operator range is
dynamic, this is a lockout risk and the value must be revisited before the hosts are relied upon — see
the open item in `execution-log.md`.

**Unverifiable from inside the guest (U2):** the OCI security list and any NSG applied to these VNICs
cannot be read without console/API access. What the guests *can* prove is the resulting behaviour, which
was measured; see §3.5.

### 3.3 Backend VM — `/etc/iptables/rules.v4` intent

Same preamble, plus:

```
-A INPUT -p tcp --dport 22 -s <ADMIN_CIDR> -j ACCEPT
-A INPUT -s 10.0.0.26/32 -p tcp --dport 8000 -j ACCEPT
-A INPUT -p tcp --dport 8000 -j REJECT
-A INPUT -p tcp --dport 111 -j REJECT
-A INPUT -j REJECT --reject-with icmp-host-prohibited
```

Defence in depth: compose **also** binds `10.0.0.33:8000`, so a firewall mistake alone cannot expose the
API to the internet; a bind mistake alone cannot either.

### 3.4 Validation

| Check | Expected |
|---|---|
| `sudo iptables -S` after `netfilter-persistent restart` | intended rules present, Docker chains present only after Docker start |
| Reboot test (Phase 3, on the destination, before data exists) | rules survive; `sshd` reachable; unpublished ports rejected |
| From BE: `nc -z -w3 10.0.0.26 443` / from FE: `nc -z -w3 10.0.0.33 8000` | succeed once the services exist |
| From an **external** vantage: FE `80/443` open, `3000/8000/5432/6379` closed | as designed |
| `ip_forward` | `1` after Docker starts, documented |
| `ss -lntp` | no `:111`; no `0.0.0.0:8000` on BE |

### 3.5 Measured cloud-side behaviour (U2 evidence, 2026-10-20)

Measured from the FE VM against the BE VM's **public** IP (a genuine inter-subnet public path):

| Probe (from FE to BE public IP) | Result |
|---|---|
| `84.12.82.239:22` | no connection |
| `84.12.82.239:8000` | no connection |
| `84.12.82.239:5432` | no connection |
| `84.12.77.251:443` (FE's own public IP, hairpin) | **`No route to host`** — the OCI VCN does not hairpin public IPs from inside the VCN; this is normal and expected, not a fault |

Interpretation: no path was observed that exposes BE's `8000`/`5432` publicly. This is consistent with
the required policy, but it is **behavioural** evidence only. The authoritative statement — which
security list rule and which NSG allow 80/443 and restrict 22 — remains console-side and is recorded as
an open item.

Two host-side findings from the same run:

1. **The stock OCI firewalls on both VMs accept port 22 from any source** (`-A INPUT -p tcp --state NEW
   --dport 22 -j ACCEPT`, no `-s`). Only the cloud layer restricts SSH today. This Phase narrows it to
   the admin `/32`.
2. The FE→BE private path delivers **all** ports (22/80/443/3000/5432/6379/8000 all connect when a
   listener exists) — so `10.0.0.0/24` has no port-level isolation. Correctness depends on container bind
   addresses plus the host firewall, exactly as designed in §3.3.

---

## 4. TLS plan (FE)

| Item | Design |
|---|---|
| Material | copy `/etc/letsencrypt` intact (both lineages), modes preserved, root-only |
| Active cert | `missioncontrol.optichosting.co.za`, RSA, expires **2027-01-06** [V] |
| Renewal | **webroot**: `certbot renew --webroot -w /var/www/letsencrypt`, `certbot.timer`, deploy hook `docker exec mc-nginx nginx -s reload` |
| ACME path | `location ^~ /.well-known/acme-challenge/ { root /var/www/letsencrypt; default_type text/plain; }` **before** the 80 → 443 redirect |
| Precondition | renewal only succeeds once DNS resolves to the FE VM; the copied cert covers the gap |
| Not carried | the source `certbot-renewal.sh` (standalone authenticator; stops containers; unwritable log) |
| Verification | `openssl x509 -noout -subject -dates` on FE; `certbot renew --dry-run` **with nginx running** |
| Fallback | DNS-01 via registrar API (introduces a credential → needs approval) **[?] U3** |
| Second lineage (`missioncontroldev`, expires 2026-11-20) | keep only if something serves it; otherwise drop **[?] U4** |

TLS termination stays at the edge. No certificate is installed on the BE VM. Traffic FE → BE:8000 is
plain HTTP **inside the VCN**; this is a deliberate, documented choice (same as today's container bridge,
but now traversing the private subnet). **[R]** If end-to-end encryption is required later, add an
internal CA — out of scope here.

---

## 5. SSH, accounts, and host hardening

| Item | Source behaviour | Destination plan |
|---|---|---|
| SSH | key-only, root login without password | copy the same `authorized_keys`, keep key-only; **no password auth** |
| fail2ban | **1.0.2**, jails `sshd` + `recidive`; reads `/var/log/auth.log` (rsyslog present) | installed on both destinations (**0.11.2**); jail `sshd` uses **`backend = systemd`**, because **`auth.log` does not exist** on the destination images (no rsyslog) — a real source/destination divergence. `recidive` not carried over (see §5.1) |
| ufw / firewalld | inactive / absent | **do not install** (persisted iptables is the control) |
| rpcbind / iscsid | running / enabled | disable `rpcbind` (**done**); leave `iscsid` (OCI image inertia) but document |
| unattended-upgrades | enabled, auto-reboot off | keep; **pin Docker version** and exclude it from auto-upgrade during the migration window **[R]** |
| Oracle Cloud Agent | monitoring, run-command, cloud-guard, custom logs | leave enabled; confirm no custom-log config points at obsolete paths |
| Time sync | `systemd-timesyncd` active | keep |
| Host users | `ubuntu` (OCI default), `billboe3` | **do not** create extra accounts; connect as `ubuntu` + key |

### 5.1 fail2ban as installed on the destinations (Phase 3b, verified)

| Aspect | Destination state |
|---|---|
| Version / service | 0.11.2, `active` + `enabled` on both VMs |
| Jail | `sshd` only; `backend = systemd`, `filter = sshd`, `port = ssh` |
| Threshold | `maxretry 5`, `findtime 10m`, `bantime 1h`, incrementing to `1w` |
| `ignoreip` (lockout protection) | `45.220.11.50`, `168.253.204.10`, `10.0.0.0/24`, `127.0.0.0/8`, `::1` |
| Log source | journald (`_SYSTEMD_UNIT=sshd.service + _COMM=sshd`) — **required**, `auth.log` absent |
| Ban action | `iptables-multiport` → `f2b-sshd` chain in the **nft**-backed filter table (live-proven) |
| Detection proof | 16 lines matched against a real captured journal sample |
| Lockout proof | 32 real `Invalid user … from 127.0.0.1` events produced; jail reported 0 failed because localhost is whitelisted |
| Persistence | enabled for boot; bans are runtime-only and do **not** appear in `rules.v4` |
| `recidive` jail | **not installed** **[R]** add later if repeated-offender escalation is wanted; requires a filter over fail2ban's own log, which is a separate hardening step and was outside the approved "SSH jail" scope |
| Password auth | **disabled** (`passwordauthentication no`) — the jail therefore catches `Invalid user`, `Failed publickey` and `maximum authentication attempts exceeded`, not `Failed password` |

---

## 6. Secrets handling

| Secret | Source state | Destination state |
|---|---|---|
| `MISSIONCONTROL_SECRET_KEY` | `.env` mode 664 + inline in compose | `.env` mode **600**, owner `ubuntu`; **byte-identical** value; no inline copy; exists on **BE only** |
| `POSTGRES_PASSWORD` | `.env` 664 | `.env` 600 |
| Agent API keys (DB) | `agents` table | travel with the dump; DB file permissions via the postgres volume |
| TLS private keys | `/etc/letsencrypt/archive`, root 0600 | same, FE only |
| SSH private keys used by plugins | `~/.ssh` in the backend container context | **not** copied unless a plugin proves it needs them; if copied, 600 and documented |
| `.env.production` (tracked) | in Git, value ≠ live key | not deployed; hygiene item in `destination-diff.md` §6 |

Transfer rules: `scp`/`rsync` over SSH only, no paste into chat/logs, no value echoed in commands, no
secret in `docker inspect` output captured to disk. Verification is by **hash comparison**, never by
printing.

---

## 7. D-F — closing `/dockhand/` on production (separate approval, not executed)

**Evidence of exposure [V]:** `GET https://missioncontrol.optichosting.co.za/dockhand/` → **200** and
`/dockhand/api/containers` → **200**, unauthenticated, with `docker.sock` mounted rw in the container.
Dockhand's own database has **0 users, 0 sessions, authentication disabled**, 0 environments, 0 git
repos; nginx logs show 326 `/dockhand` requests, of which 282 are not from our audit `curl` — i.e. real
browser traffic exists (at least one owner visit on 14 Oct that produced 404s on the API sub-path).

**Proposed change (exact):** replace the three dockhand routing blocks with a single explicit **deny**
that covers both the UI and its API, and closes the redirect:

```diff
--- a/nginx/default.conf
+++ b/nginx/default.conf
@@
-    # Dockhand - Docker Management UI (path-based routing)
-    location /dockhand/ {
-        proxy_pass http://dockhand:3000/;
-        proxy_http_version 1.1;
-        proxy_set_header Host $host;
-        proxy_set_header X-Real-IP $remote_addr;
-        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
-        proxy_set_header X-Forwarded-Proto $scheme;
-        proxy_set_header Upgrade $http_upgrade;
-        proxy_set_header Connection "upgrade";
-        proxy_buffering off;
-        proxy_read_timeout 3600s;
-        proxy_connect_timeout 60s;
-        # Inject <base> tag for SPA sub-path navigation
-        sub_filter '<head>' '<head><base href="/dockhand/">';
-        # Rewrite asset paths for SPA under sub-path
-        sub_filter 'href="/' 'href="/dockhand/';
-        sub_filter 'src="/' 'src="/dockhand/';
-        sub_filter_once off;
-        sub_filter_types text/html text/css application/javascript;
-    }
-
-    location = /dockhand {
-        return 301 /dockhand/;
-    }
+    # Dockhand retired from public routing (2026-10-20).
+    # Regex location matches /dockhand, /dockhand/ and /dockhand/<anything>
+    # (including /dockhand/api/containers). The container, its database and its
+    # volumes are untouched and remain reachable only on the Docker network.
+    location ~ ^/dockhand(/|$) {
+        return 404;
+    }
```

Rationale for the regex location rather than deleting the block:

| Aspect | Why |
|---|---|
| Coverage | `location ~ ^/dockhand(/|$)` matches the exact path, the trailing-slash path **and** every sub-path, so the API surface cannot be reached by omitting or adding a slash |
| Not a broad change | Nothing else in the config matches `^/dockhand`; `/api/`, `/` and `/health` are untouched |
| Response | `404` (not `403`) avoids confirming that an administrative interface exists at that path |
| Reversibility | The whole change is three deletions plus one four-line block; the previous file is preserved by hash and in git |
| Scope discipline | The `dockhand` service, `dockhand_data` volume and its SQLite state are **not** stopped, removed or modified |

| Aspect | Detail |
|---|---|
| Reason | unauthenticated administrative UI with root-equivalent Docker access on a public host |
| Impact | `/dockhand`, `/dockhand/`, `/dockhand/api/*` return **404**; the container keeps running (reachable only from inside the Docker network); no other route changes |
| Validation | `docker exec missioncontrol-nginx-1 nginx -t` **before** reload; then `curl` probes for `/dockhand`, `/dockhand/`, `/dockhand/api/containers` → 404 and `/`, `/api/v1/health/live`, `/api/v1/health/ready`, `/api/v1/version`, `/api/docs`, websocket → unchanged |
| Rollback | restore the previous `nginx/default.conf` (sha256 `734f40e4…`, content preserved in commit `75a8280`), `nginx -t`, reload — < 1 minute |
| Downtime | none (reload, not restart) |
| Approval | **APPROVED 2026-10-20** (owner decision D-F). Executed as a separate operation from the migration; evidence recorded in `execution-log.md` |
| Execution prerequisite | the small `@net` rate limit means rapid repeated probes from one IP can themselves return 429 — probes must be spaced and the result interpreted accordingly |

Alternative if a Docker UI must remain: run it on the BE VM bound to `127.0.0.1`, reachable only through
an SSH tunnel, with authentication enabled. **[R]** Do not proxy it publicly again.

---

## 8. Migration-window security notes

- The destination hosts receive no production traffic until cutover; their 80/443 listening state can be
  validated with a hosts-file override (`curl --resolve`) instead of DNS.
- The source host keeps its current (permissive) posture during the window. Do not "improve" it
  mid-migration except under D-F approval.
- Agent fleet authentication is per-agent API key; nothing in the split changes the trust model, because
  agents keep talking to the same public hostname through nginx.
- Rate limiting / WAF: none today; **not** introduced by this migration. If wanted later, it belongs at the
  edge nginx and needs its own change control.

---

## 9. Security findings carried forward (unchanged by this phase)

| ID | Finding | Owner decision needed |
|---|---|---|
| S1 | `/dockhand/` public + unauthenticated + `docker.sock` | D-F (approve closure) |
| S2 | `/api/docs` and `/api/openapi.json` public | U3 (block on destination?) |
| S3 | `docker.sock` rw in backend | U7 (accept for cutover, harden later) — recommendation: accept, then socket-proxy |
| S4 | `.env` mode 664 on source | fix on source as a separate change; 600 on destinations |
| S5 | `.env.production` tracked in Git | separate repo hygiene change |
| S6 | `rpcbind:111` listening on destinations | disable in Phase 3 |
| S7 | No host-level IDS/WAF anywhere | out of scope; note as residual risk |
