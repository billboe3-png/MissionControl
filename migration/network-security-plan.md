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

**Unresolved (must be read from the OCI console before Phase 7):** whether the public IPs are
**reserved**, the exact ingress rules (source scopes for 22, any explicit 8000 rule) and whether a
network security group applies in addition to the security list. These cannot be read from inside the
guest. **[?] U1/U2**

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
| From BE: `nc -z -w3 10.0.0.26 443` / from FE: `nc -z -w3 10.0.0.33 8000` | succeed |
| From an **external** vantage: FE `80/443` open, `3000/8000/5432/6379` closed | as designed |
| `ip_forward` | `1` after Docker starts, documented |
| `ss -lntp` | no `:111`; no `0.0.0.0:8000` on BE |

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
| fail2ban | sshd + recidive, 184 bans | install on FE and BE with the repo's `deploy/fail2ban-*` jails |
| ufw / firewalld | inactive / absent | **do not install** (persisted iptables is the control) |
| rpcbind / iscsid | running / enabled | disable `rpcbind`; leave `iscsid` (OCI image inertia) but document |
| unattended-upgrades | enabled, auto-reboot off | keep; **pin Docker version** and exclude it from auto-upgrade during the migration window **[R]** |
| Oracle Cloud Agent | monitoring, run-command, cloud-guard, custom logs | leave enabled; confirm no custom-log config points at obsolete paths |
| Time sync | `systemd-timesyncd` active | keep |
| Host users | `ubuntu` (OCI default), `billboe3` | **do not** create extra accounts; connect as `ubuntu` + key |

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

**Proposed change (exact):**

```diff
--- a/nginx/default.conf
+++ b/nginx/default.conf
@@
-    location /dockhand/ {
-        proxy_pass http://dockhand:3000/;
-        ...
-    }
-    location = /dockhand {
-        return 301 /dockhand/;
-    }
```

i.e. delete the `/dockhand/` location, the `sub_filter` directives that only serve it, and the
`/dockhand` redirect. Leave the `dockhand` **container and volume** running and untouched.

| Aspect | Detail |
|---|---|
| Reason | unauthenticated administrative UI with root-equivalent Docker access on a public host |
| Impact | `/dockhand/` returns 404; no other route changes; the container keeps running (reachable only from inside the Docker network) |
| Validation | `docker exec missioncontrol-nginx-1 nginx -t`; reload; `curl -o /dev/null -w '%{http_code}' https://…/dockhand/` → 404; `/`, `/api/v1/health/live` still 200; websocket still works |
| Rollback | restore the previous `nginx/default.conf` (sha256 `734f40e4…`), `nginx -t`, reload — < 1 minute |
| Downtime | none (reload, not restart) |
| Approval | **explicit owner approval required before touching production** |

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
