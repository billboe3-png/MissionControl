# OCI Firewall Remediation — Exact Console Steps

**Purpose:** fix the Phase 5 blocker. Active probes (2026-10-20) proved that **all TCP between the two
destination VMs is dropped at the OCI cloud layer**, while ICMP passes and L2 ARP works. The frontend VM
must reach the backend API at `10.0.0.33:8000`, so deployment cannot proceed until this is corrected.

**This document contains console steps only.** It is written for the **owner** to execute (console/API access
is not available to the migration agent, and U2 forbids broadening rules from inside a guest).

**Labels:** `[V]` verified from the guest · `[?]` unresolved / console-dependent · `[R]` recommendation.

---

## 0. What we know for certain [V]

| Fact | Value |
|---|---|
| Region | `af-johannesburg-1` |
| Compartment | tenancy root: `ocid1.tenancy.oc1..aaaaaaaazs2muhc7rtots6uqn2jguxlmw7xe6avqhyfa7oeqy2yuquxnbtgq` |
| Availability domain | `Ihhc:AF-JOHANNESBURG-1-AD-1` |
| Frontend instance | `Mission-Control-Frontend` · `ocid1.instance.oc1.af-johannesburg-1.anvg4ljrorhmptqc3uamehbojdaluy22hqb6mddvr2uvz47ubqgb6vs6yssa` |
| Backend instance | `Mission-Control-Backend` · `ocid1.instance.oc1.af-johannesburg-1.anvg4ljrorhmptqcn6sgyhvtgcwslbng656z7kk6tfjfmt56z37wgcndjz3a` |
| Frontend VNIC | `ocid1.vnic.oc1.af-johannesburg-1.abvg4ljrzde4bjhns3fp2agr7up5c553ggigfzj723xxqyahor6ootrzxixa` (`10.0.0.26`, MAC `02:00:17:02:87:4B`) |
| Backend VNIC | `ocid1.vnic.oc1.af-johannesburg-1.abvg4ljr35fke66lp52ghzdqivf5dzmxev773niv6evjqnsbl6xo2khwhh2a` (`10.0.0.33`, MAC `02:00:17:02:19:6D`) |
| Subnet CIDR (both VNICs report the same) | `10.0.0.0/24`, virtual router `10.0.0.1` |
| Observed failure | FE→BE and BE→FE TCP on **every** port = `No route to host`; ICMP OK; ARP OK; guest REJECT counters do not increment |

**Interpretation [?]:** because the guest firewalls demonstrably do not see the packets, the drop is a
**security list and/or network security group (NSG)** applied at the VCN/subnet/VNIC. The rule set supplied
by the owner (all-protocols `10.0.0.0/16`, TCP 22 `10.0.0.0/16`) *should* permit this traffic, so either a
**different list is in force**, an **NSG overrides it**, or the rules are attached to a **different
subnet/VCN**. All three are console-visible; Step 3 below disambiguates.

---

## 1. Preconditions

- Sign in to the OCI Console as a user with **manage** rights on networking in the root compartment.
- Region selector (top-right) must read **South Africa Central (Johannesburg)** / `af-johannesburg-1`.
- Do this **before** any further deployment work.

> ⚠️ **Do not** add `0.0.0.0/0` as the source for port 8000 or 22. All sources below are private
> (`10.0.0.0/24`). This is a *targeted permit*, not a broadening (satisfies U2).

---

## 2. Locate the exact resources (console navigation)

1. **Menu → Networking → Virtual Cloud Networks.**
2. Ensure **Compartment = the root compartment**
   (`ocid1.tenancy.oc1..aaaaaaaazs2muhc7rtots6uqn2jguxlmw7xe6avqhyfa7oeqy2yuquxnbtgq`).
   The VCN hosting `10.0.0.0/24` may be listed as a resource in the root compartment.
3. Click the VCN whose CIDR contains `10.0.0.0/24`.
4. Click the **subnet** whose CIDR is `10.0.0.0/24` (this is the subnet for both VNICs).

**Record for the report:** the **VCN name**, the **subnet name**, and the **Subnet OCID**, plus the names of
the **security list(s)** attached to that subnet.

---

## 3. Diagnose which mechanism is blocking (do this first)

### 3a. Inspect the subnet's security lists (the usual mechanism)

1. On the subnet page, under **Resources → Security Lists**, click the attached security list
   (a subnet usually has one; OCI's default is *Default Security List for `<vcn>`*).
2. Read the **Ingress Rules**. Compare against the four required rules in §4.

### 3b. Check for a Network Security Group (NSG) — the common override

1. **Menu → Networking → Virtual Cloud Networks → your VCN → Resources → Network Security Groups.**
2. Open each NSG and check its **Security rules → Ingress**.
3. Note any NSG that has a rule matching `10.0.0.26` / `10.0.0.33`.
4. **Go to each destination instance → Resources → Attached VNICs → click the VNIC → look at
   "Network Security Groups".** If an NSG is attached, it is evaluated **in addition to** the security
   list, and a missing permit there will block the traffic even if the security list allows it.

> If an NSG is attached to either VNIC and does not itself permit `10.0.0.26/32 → TCP 8000`, that alone
> explains the failure. Fix the NSG (add the same rules as §4) **or** detach the NSG if it is unused.

### 3c. Confirm both VNICs are on the *same subnet*

- **Compute → Instances → `Mission-Control-Frontend` → Attached VNICs**: confirm the subnet name/OCID.
- Repeat for `Mission-Control-Backend`.
- If they are on **different subnets**, security lists must **both** permit the traffic (ingress on the
  backend's list, egress on the frontend's list — see §4 egress note).

---

## 4. Add the required ingress rules

Add these to **the security list(s) attached to the subnet** (and to any attached NSG). Ingress is
evaluated against the **destination** VNIC.

| # | Stateless? | Source Type | Source | Protocol | Destination Port | Description |
|---|---|---|---|---|---|---|
| A | No (stateful) | CIDR Block | `10.0.0.26/32` | TCP | `8000` | MC-FE edge → MC-BE API |
| B | No (stateful) | CIDR Block | `10.0.0.0/24` | TCP | `22` | intra-VCN SSH (admin/validation) |
| C | No (stateful) | CIDR Block | `10.0.0.0/24` | ICMP | (ICMP Type/Code: `3,4` or blank for all) | intra-VCN ping (already works; add for completeness) |

**Optional, only if you want BE→FE TCP for validation:** add a mirrored rule with
Source `10.0.0.33/32`, Protocol TCP, Port `443`. Not required by the architecture.

**Click-by-click (security list):**
1. Subnet → **Security Lists** → click the list → **Add Ingress Rules**.
2. For Rule A: **Stateless = unchecked**; **Source Type = CIDR**; **Source = `10.0.0.26/32`**;
   **IP Protocol = TCP**; **Destination Port Range = `8000`**; Description `MC-FE to MC-BE API`;
   **Add Ingress Rule**.
3. **Add Ingress Rules** again for Rule B (`10.0.0.0/24`, TCP, `22`).
4. Optionally Rule C (ICMP, `10.0.0.0/24`). Click **Add Ingress Rules**.

**Egress note:** OCI's default security list has an "allow all" egress rule and both VNICs' egress works
(egress to `https://example.com` returned 200, and to the metadata service). **No egress change is normally
needed.** If diagnosis in §3c shows a custom restrictive egress list on the frontend subnet, add an egress
rule: Destination `10.0.0.33/32`, TCP, port `8000`.

---

## 5. Verify from the instance side (agent will run this)

After the rules are saved (changes are immediate), the migration agent will re-run:

```bash
# on FE (10.0.0.26)
timeout 5 bash -c 'cat < /dev/null > /dev/tcp/10.0.0.33/8000' && echo OPEN || echo blocked
# on FE, full matrix
for p in 22 8000; do timeout 3 bash -c "cat < /dev/null > /dev/tcp/10.0.0.33/$p" && echo "$p OPEN" || echo "$p blocked"; done
```

**For the step to pass:** FE→BE `22` and `8000` must report **OPEN**. BE has no listener on 8000 until the
backend container is deployed, so at this verification stage the connection may still be *refused*
(fast `Connection refused`) rather than *times out / no route* — **"host unreachable / no route" means the
rule is still not effective; "connection refused" means the network path is now open** and we can deploy.

---

## 6. What NOT to do

- **Do not** set the source of any rule to `0.0.0.0/0` for ports 8000 or 22.
- **Do not** remove the existing admin SSH rules (`45.220.11.50/32`, `168.253.204.10/32`) — they keep you
  from locking yourself out.
- **Do not** disassociate the Default Security List if it is the only one providing 80/443 for the frontend.
- **Do not** change the frontend subnet's 80/443 rules.

---

## 7. Report back

When done, paste (or record in `execution-log.md`):

1. The **VCN name**, **subnet name/OCID**.
2. The **security list name** and its full **ingress rule table** (after the change).
3. **Whether an NSG was attached** to either VNIC, and if so its rules after the change.
4. Confirmation that no `0.0.0.0/0` rule was added.

Then the agent will re-run the connectivity checks and, on a green result, **resume Phase 5** (transfer
images + `.env` + TLS, deploy the backend, validate, then the frontend).

---

## 8. If the rules look correct but traffic is still blocked

Work down this list (all console-side):

1. **Wrong compartment/VCN.** Confirm the VCN you edited is the one containing both instances
   (§2 step 2).
2. **NSG override.** Re-check §3b — an attached NSG that lacks the permit blocks regardless of the list.
3. **Rule ordering / duplicate deny.** OCI security lists are evaluated as OR (any allow wins); a deny is
   not expressible, so a "deny" cannot be the cause. If it is still blocked with correct allows, suspect an
   **NSG** or a **different subnet**.
4. **Instance-level NSG added later.** Check `Compute → Instance → Attached VNICs → NSG` again after saving.
5. **Subnet is regional vs AD-specific.** Confirm both instances' VNICs reference the *same* subnet OCID.
6. **Escalate to OCI support** with: the VNIC OCIDs, the subnet OCID, the rule table, and the guest-side
   probe output (ICMP OK, TCP `No route to host`, ARP REACHABLE, guest REJECT counters static).

---

## 9. Appendix — OCI CLI alternative (if you prefer CLI over console)

> **Status [?]:** the migration agent found an API key at `~/.oci/oci_api_key.pem` on the source host but
> **no `~/.oci/config`** and no `oci` CLI. The CLI needs five values the agent does not have and must not
> guess: `user` OCID, `tenancy` OCID (known: see §0), `fingerprint`, `region` (known: `af-johannesburg-1`),
> and the key file. Supply them (or run these yourself) and the agent can execute the verification.

### 9.1 One-time setup (on the source host or your workstation)

```bash
# install the CLI
pip3 install --user oci-cli            # or: bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# create ~/.oci/config  (fill user/fingerprint from the console: Identity → Users → API Keys)
mkdir -p ~/.oci && chmod 700 ~/.oci && cat > ~/.oci/config <<'EOF'
[DEFAULT]
user=ocid1.user.oc1..<YOUR_USER_OCID>
fingerprint=<YOUR_KEY_FINGERPRINT>
tenancy=ocid1.tenancy.oc1..aaaaaaaazs2muhc7rtots6uqn2jguxlmw7xe6avqhyfa7oeqy2yuquxnbtgq
region=af-johannesburg-1
key_file=~/.oci/oci_api_key.pem
EOF
chmod 600 ~/.oci/config
```

### 9.2 Find the subnet and its security lists

```bash
COMP=ocid1.tenancy.oc1..aaaaaaaazs2muhc7rtots6uqn2jguxlmw7xe6avqhyfa7oeqy2yuquxnbtgq

# VCNs in the compartment
oci network vcn list --compartment-id "$COMP" --query 'data[].{name:"display-name",id:id,cidr:"cidr-block"}' --output table

# subnets (find the one with 10.0.0.0/24)
oci network subnet list --compartment-id "$COMP" \
  --query 'data[?("cidr-block"==`10.0.0.0/24`)].{name:"display-name",id:id,sl:"security-list-ids"}' --output json
```

### 9.3 Inspect and add a rule (example: FE → BE :8000)

```bash
SL=ocid1.securitylist.oc1.af-johannesburg-1.<YOUR_SL_OCID>

# current ingress rules
oci network security-list get --security-list-id "$SL" \
  --query 'data."ingress-security-rules"' --output json

# add the required rule (source 10.0.0.26/32, TCP 8000) — NOTE: this replaces the list,
# so fetch the existing rules, append, and update in one call:
oci network security-list update --security-list-id "$SL" \
  --ingress-security-rules '[ ...EXISTING RULES..., {"source":"10.0.0.26/32","protocol":"6","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":8000,"max":8000}},"description":"MC-FE to MC-BE API"} ]'

# add intra-VCN SSH (10.0.0.0/24 TCP 22) with protocol "6" and destinationPortRange 22/22
# add intra-VCN ICMP (10.0.0.0/24 protocol "1", no tcpOptions)
```

> ⚠️ `security-list update` **replaces** the whole rule set. Always fetch the current rules first and
> append — never overwrite with only the new rule, or you will drop 80/443 and lock out SSH.

### 9.4 Discover and inspect NSGs

```bash
oci network nsg list --compartment-id "$COMP" --query 'data[].{name:"display-name",id:id}' --output table

# which NSGs are on each VNIC (this is the common blocker)
oci network vnic get --vnic-id ocid1.vnic.oc1.af-johannesburg-1.abvg4ljrzde4bjhns3fp2agr7up5c553ggigfzj723xxqyahor6ootrzxixa \
  --query 'data."nsg-ids"'
oci network vnic get --vnic-id ocid1.vnic.oc1.af-johannesburg-1.abvg4ljr35fke66lp52ghzdqivf5dzmxev773niv6evjqnsbl6xo2khwhh2a \
  --query 'data."nsg-ids"'
```

If NSGs are returned, add a matching rule to each:

```bash
NSG=ocid1.networksecuritygroup.oc1.af-johannesburg-1.<YOUR_NSG_OCID>
oci network nsg rules add --nsg-id "$NSG" --security-rules '[{"direction":"INGRESS","source":"10.0.0.26/32","protocol":"6","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":8000,"max":8000}},"description":"MC-FE to MC-BE API"}]'
```

### 9.5 Re-verify

```bash
# from FE
timeout 5 bash -c 'cat < /dev/null > /dev/tcp/10.0.0.33/8000' && echo OPEN || echo blocked
```

Then report the same four items as §7.

