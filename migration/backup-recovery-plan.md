# Backup & Recovery Plan — Mission Control 2-VM Migration

**Status:** PLAN FOR APPROVAL. **No production backup has been created or transferred.**
**Owner decision U6 (2026-10-20):** back up to the owner's **local Windows machine**; encrypt sensitive
artefacts; never print secrets; verify by SHA-256; document location, access control, encryption and
recovery-key custody; include a scratch-database restore test verifying schema, row counts and credential
decryption; document the single-location risk.

**Labels:** **[V]** verified by command · **[A]** assumption · **[?]** unresolved · **[R]** recommendation.

---

## 1. Scope — what is backed up and what is not

| # | Artefact | Source path | In scope | Why |
|---|---|---|---|---|
| 1 | **PostgreSQL database** `mission_control` | `missioncontrol-postgres-1:/var/lib/postgresql/data` → dumped | **Yes** | The only irreplaceable state (441 MB) |
| 2 | **Database roles/globals** (incl. `mission_control` role + password) | `pg_dumpall --globals-only` | **Yes** | Needed to recreate a working cluster; tiny |
| 3 | **Production `.env`** (9 keys: `MISSIONCONTROL_SECRET_KEY` Fernet, `POSTGRES_PASSWORD`, etc.) | `/opt/MissionControl/.env` | **Yes, encrypted** | Fernet key decrypts 33 stored credentials. Losing it silently breaks every integration |
| 4 | **TLS material** (both lineages) | `/etc/letsencrypt/` (228 KB) | **Yes, encrypted** | `privkey.pem` files are secrets; renewal configs needed by U4 |
| 5 | Application source revision | repo branch/tag + digests | **No** (already in Git) | Reproducible from Git; recorded as a pin |
| 6 | Redis data | `missioncontrol-redis-1` | **No** (documented as empty) | `dbsize = 0` **[V]** — nothing to back up; a stub snapshot is taken for completeness |
| 7 | Docker images | — | **No** | Rebuilt from source + `build-and-transfer.md` digests |
| 8 | `agent_commands` (421 MB, 98,173 rows) | inside the DB | **Yes** | Part of the database dump; owner decision D-D |
| 9 | Uploads / user files | `backend/app/data` (4 KB, empty) | **No** | No uploads exist **[V]** |

**Explicitly excluded:** the `dockhand` container/volumes (not migrated — D-B/U5), the second
`missioncontrol2_*` volume set (a stale prior deployment, not the live one — recorded but not backed up),
and any host filesystem image.

---

## 2. Required space

Measured on the source, 2026-10-20:

| Item | Raw size | Note |
|---|---|---|
| Database (as reported by PostgreSQL) | **439 MB** | `pg_database_size` |
| Postgres data directory on disk | 502 MB | includes WAL, `base/`, `pg_wal` |
| `agent_commands` share | 421 MB | 98,173 rows, TOAST-heavy |
| `/etc/letsencrypt` | 228 KB | both lineages |
| `.env` | 298 bytes | 9 keys |

**Estimate by artefact (post-compression, encrypted):**

| Artefact | Estimated on-disk (local) | Basis |
|---|---|---|
| `db-full.dump` (`pg_dump -Fc`, zlib-compressed + encrypted) | **~150–250 MB** | `-Fc` compresses the 421 MB TOAST/`agent_commands` table heavily; the encrypted container adds no measurable size |
| `globals.sql` | < 5 KB | roles only |
| `.env` (+ hash) | < 2 KB | encrypted |
| `letsencrypt.tar` (+ hash) | ~120 KB | 228 KB raw → compressed/encrypted |
| Checksums + manifest | < 50 KB | text |
| **Total estimate** | **≈ 200–300 MB** | leave generous headroom |

**[V] Local free space: 22.0 GB on `C:` (single volume, 475 GB total).** Required ≈ 0.3 GB, so space is
**not** a constraint — but see §7 (single-location risk) and the recommendation to keep two local rotations
(≈0.6 GB total).

**[?] Residual:** the exact `-Fc` size is only known after a real dump. The plan measures it at execution
time and records both raw and compressed/encrypted sizes in the manifest before transfer.

---

## 3. Destination (exact path)

```
C:\Backup\MissionControl\
├── 2026-10-20T<UTC>\
│   ├── db-full.dump.enc            # pg_dump -Fc | zstd | gpg --symmetric
│   ├── db-full.dump.enc.sha256     # SHA-256 of the encrypted file
│   ├── globals.sql.enc
│   ├── globals.sql.enc.sha256
│   ├── missioncontrol.env.enc      # the production /.env
│   ├── missioncontrol.env.enc.sha256
│   ├── letsencrypt.tar.enc         # both certificate lineages
│   ├── letsencrypt.tar.enc.sha256
│   ├── MANIFEST.txt                # non-secret metadata (see §6)
│   └── RESTORE-KEY-CHECK.txt       # key-check hint, NOT the key (see §5)
└── 2026-10-27T<UTC>\               # next rotation (recommended)
```

**[R]** Keep **two** timestamped sets locally and delete the third-oldest. Rationale: a single copy is one
`rm` away from total loss, and the cost is only ~0.3 GB.

---

## 4. Encryption method

**Constraint discovered [V]:** the local Windows machine has **no `7z`, `gpg`, or `openssl`** — only
`tar`, `ssh-keygen`, `certutil`. Therefore **all compression and encryption happens on the source host**
before transfer, and the local machine only verifies and stores.

| Step | Tool | Command (source) | Purpose |
|---|---|---|---|
| Dump | `pg_dump -Fc` (v16.14) | `pg_dump -Fc -Z6 -U mission_control mission_control -f db-full.dump` | Consistent, restorable, compressed custom format |
| Compress | `zstd -19` (v1.5.5) | `zstd -19 -T0 db-full.dump -o db-full.dump.zst` | Better ratio than `-Fc`'s zlib on TOAST data |
| Encrypt | **`gpg --symmetric --cipher-algo AES256`** (GnuPG 2.4.4) | `gpg --symmetric --cipher-algo AES256 --s2k-mode 3 --s2k-count 65011712 -o db-full.dump.enc db-full.dump.zst` | AEAD-capable symmetric encryption with a strong S2K; passphrase never on the command line (see §5) |
| Checksum | `sha256sum` (coreutils 9.4) | `sha256sum db-full.dump.enc > db-full.dump.enc.sha256` | Integrity of the **transferred** file |

**Why GPG symmetric rather than `openssl enc`:** GPG performs repeated-passphrase key derivation
(`--s2k-mode 3`, high iteration count) and is the tool with a documented, reviewable passphrase KDF.
`openssl enc` with a password has weaker KDF defaults and a history of misuse. **[R]** use GPG.

**Why AES-256 rather than a public-key scheme:** the owner is the only recipient and wants a
passphrase-protected copy; symmetric avoids managing an extra keypair. If the owner later wants keys in a
hardware token, the plan supports substituting `gpg --encrypt -r <keyid>` without other changes.

**`zstd` before `gpg`** (not after): compressing plaintext then encrypting is safe; encrypting then
compressing leaks nothing but wastes space, because ciphertext is incompressible.

**The Fernet key and TLS private keys are inside the encrypted payloads.** They are never transmitted or
stored in the clear. The `.env` copy is encrypted with the same passphrase.

---

## 5. Recovery-key handling and custody

This is the single most important part of the plan.

| Aspect | Design |
|---|---|
| **What the key is** | A high-entropy passphrase (recommend **≥ 32 characters**, generated with `openssl rand -base64 48` *on the source*, or a memorable 6-word diceware phrase) that unlocks all four `.enc` files |
| **How it is entered** | Interactively via GPG's `--pinentry-mode loopback` prompt reading from `/dev/tty`, or `gpg --passphrase-fd 0` fed from a file descriptor. **Never** as an argv argument (argv is visible in `ps`) and **never** in shell history |
| **Where it is stored** | **[R] Two independent copies, neither on the backup disk alone:** (1) the owner's password manager entry "MissionControl backup <date>"; (2) a sealed written copy in a physically separate location (safe / off-site document). Not in the same directory tree as the backups |
| **What is NOT stored** | The passphrase is not written into `MANIFEST.txt`, not committed to Git, not emailed, not printed to any terminal or log |
| **Key-loss consequence** | All `.enc` files become permanently unrecoverable. This is documented here so the owner can weigh it: the backups are worthless without the passphrase |
| **Key-rotation** | Re-encrypt by decrypting and re-running §4. A key change is a new timestamped directory |
| **Verification of the key** | `RESTORE-KEY-CHECK.txt` stores a **non-secret** check: `gpg --print-md SHA256` of a fixed known string as recovered *after* decrypting the passphrase-only test blob. It lets the owner confirm a passphrase is correct without a full restore. It reveals nothing usable to an attacker |

**[A]** The source host's Fernet key must **also** be preserved independently of the backup passphrase:
the backup is only useful if both the passphrase *and* the Fernet key are available. The Fernet key lives
inside the encrypted `.env`; the plan records its **hash** (not value) in the manifest to prove which key
was backed up. **[R]** store a second copy of the Fernet key in the same password manager as the passphrase.

---

## 6. Manifest contents (non-secret)

`MANIFEST.txt` records, and nothing else:

- UTC date, source host, source revision (`git rev-parse HEAD`), branch
- Alembic head (`h7h8h9i1j2k3`) and `alembic_version.version_num` **[V]**
- PostgreSQL server version (`16.14`) and `pg_dump` format/compression flags
- Raw and encrypted sizes of each artefact
- **SHA-256 of each encrypted artefact** and of each source file *before* encryption where applicable
- **SHA-256 of the Fernet key** (hash only — proves which key was captured, exposes nothing)
- Row counts for the restore test baseline: `agent_commands` 98,173 · `agent_remote_targets` 16 ·
  `veeam_backup_servers` 15 · `integration_profiles` 6 **[V]**
- `dbsize`/`archive_mode` (`off`), confirming the dump is the sole recovery point of its own
- The line: *"Passphrase is NOT in this file. It is in the owner's password manager and a sealed off-line copy."*

---

## 7. Single-location risk (owner's explicit instruction)

The owner chose the **local Windows machine** as the destination. **[R]** the plan does **not** substitute
a cloud or NAS destination.

**Documented risk:** if this one machine is lost, stolen, or its disk fails, **the only copy of the
backup is gone**, together with the local `C:` drive. The production source remains the live system, but
there would be **zero independent recovery copy**, and no point-in-time recovery exists anywhere
(`archive_mode = off`, no WAL archive) **[V]**.

**Mitigations within the owner's stated choice:**
1. Two local rotations (§3) so one deletion or corruption does not destroy both.
2. Copies kept on a **separate physical disk where available** — **[?]** this machine has a single volume
   (`C:` only) **[V]**, so this is not currently possible without an external drive.
3. **[R]** the owner add at least one of: an external USB drive, a NAS, or a second machine, and copy the
   timestamped directory there. This is the minimum to make the backup survivable.
4. The passphrase (and Fernet key) stored *off* the same machine (§5).

If the owner is content with the single-location exposure, the plan proceeds as written and the risk is
recorded in `execution-log.md` as accepted.

---

## 8. Transfer procedure (prepared, NOT executed)

Transfer is over SSH with the existing key; the encrypted files are already safe to move.

```bash
# on the source, after §4 steps produce the .enc files and .sha256 files
ts=$(date -u +%Y%m%dT%H%M%SZ); stage=/tmp/mc-backup-$ts; mkdir -p "$stage"
# ... artefacts written into "$stage" ...
tar -C "$stage" -cf /tmp/mc-backup-$ts.tar mc-backup-$ts
```

```powershell
# on the local Windows machine
ssh billboe3@34.35.177.209 "cat /tmp/mc-backup-<ts>.tar" > "$env:TEMP\mc-backup-<ts>.tar"
New-Item -ItemType Directory -Force "C:\Backup\MissionControl\<ts>" | Out-Null
tar -xf "$env:TEMP\mc-backup-<ts>.tar" -C "C:\Backup\MissionControl"
# verify integrity locally
Get-ChildItem "C:\Backup\MissionControl\<ts>\*.enc" | ForEach-Object {
  $want = (Get-Content "$($_.FullName).sha256").Split(' ')[0]
  $got  = (certutil -hashfile $_.FullName SHA256 | Select-Object -Index 1).Replace(' ','')
  if ($want -eq $got) { "OK   $($_.Name)" } else { "FAIL $($_.Name)" }
}
```

`certutil -hashfile … SHA256` is used because the machine has no `sha256sum`; it is a Windows built-in and
produces the same digest. **[V]**

**[R]** transfer with `rsync` instead of `cat` where available, so a partial transfer can resume, and
compare the SHA-256 **after** transfer before deleting the source-side staging copies.

---

## 9. Restore test (scratch database)

Executed on the **destination backend VM** (or a throwaway container on the source) so production is never
touched. **[R]** run it on the migration's BE VM inside a scratch compose project with an empty volume.

| Step | Command (sketch) | Pass criterion |
|---|---|---|
| 1. Start scratch cluster | `docker run -d --name mc-restoretest -e POSTGRES_PASSWORD=… -e POSTGRES_USER=mission_control -e POSTGRES_DB=mission_control_test postgres:16-alpine` | container healthy |
| 2. Decrypt | `gpg --decrypt db-full.dump.enc \| zstd -d \| pg_restore -l` | header/`-l` lists objects |
| 3. Restore roles | `psql -f globals.sql` into the scratch cluster | `\du` shows `mission_control` |
| 4. Restore DB | `gpg -d db-full.dump.enc \| zstd -d \| pg_restore -d mission_control_test --no-owner --no-privileges` | exit 0, no error lines |
| 5. **Schema check** | `select version_num from alembic_version` | equals **`h7h8h9i1j2k3`** |
| 6. **Row-count check** | counts for the 4 verification tables | equals §6 baseline exactly |
| 7. **Credential decryption check** | point a scratch backend at the scratch DB with the restored `.env`; call one integration endpoint or run a one-shot `Fernet(secret_key).decrypt(row.encrypted_value)` for samples from `agent_remote_targets`, `veeam_backup_servers`, `integration_profiles` | **all sampled rows decrypt without `InvalidToken`** |
| 8. Tear down | `docker rm -f mc-restoretest`; delete the scratch volume | scratch gone, production untouched |

**Step 7 is the check that catches the classic silent failure:** a *different but valid* Fernet key
restores the database perfectly and only fails later, at first use of each integration. The plan therefore
tests decryption explicitly rather than relying on a successful restore.

**Row-count baselines are captured at dump time**, not copied from this document, so they are always the
set that was actually dumped.

---

## 10. Verification checklist (all must pass before the plan is considered complete)

| # | Check | Evidence to record |
|---|---|---|
| 1 | All four artefacts present and non-zero | `ls -l` listing |
| 2 | Every `.sha256` matches its file locally | `certutil` comparison output |
| 3 | `pg_restore -l` parses the dump without a passphrase | command output |
| 4 | Scratch restore completes, exit 0 | restore log |
| 5 | Alembic version matches `h7h8h9i1j2k3` | query result |
| 6 | All row counts match the captured baseline | query results |
| 7 | Sampled encrypted credentials decrypt with the restored Fernet key | decryption result |
| 8 | TLS lineages both present in the restored tarball | `tar -tf` listing |
| 9 | Manifest written and complete | file contents |
| 10 | Passphrase verified against `RESTORE-KEY-CHECK.txt` | check result |

Only after all ten pass is the backup set considered **verified**.

---

## 11. What this plan does NOT provide

- **No point-in-time recovery.** `archive_mode = off`, no WAL archiving **[V]**. Recovery is to the moment
  of the dump only.
- **No continuous replication.** Recovery point objective = time of last manual backup.
- **No automated schedule.** Every backup is operator-initiated and approved; no cron is created by this
  plan.
- **No encryption at rest on the source** while the dump is staged in `/tmp` — the staging window is short
  and the source is access-controlled, but the plaintext dump briefly exists on disk. **[R]** stage in a
  `600` directory owned by `billboe3` and delete immediately after transfer and verification.

---

## 12. Approval request

I am **stopping here** and requesting explicit approval before creating or transferring any production
backup. On approval, execution order is: §4 (dump → compress → encrypt) → §6 (manifest) → §8 (transfer)
→ §10 (verify) → §9 (scratch restore test) → record in `execution-log.md`.

**Open questions for the owner:**

| ID | Question | Recommendation |
|---|---|---|
| B1 | Accept the single-location risk as-is, or add an external drive / second machine? | **Add a second physical copy** (§7, mitigation 3) |
| B2 | Passphrase storage: password manager + sealed written copy, or a different custody method? | password manager **and** sealed off-line copy |
| B3 | Run the restore test on the destination BE VM, or on a throwaway container on the source? | destination BE VM (matches the real target) |
| B4 | Backup cadence and retention (the plan creates none automatically) | daily while migration is active; keep 2 rotations |
| B5 | Is the destructive `gpg` passphrase acceptable, or is a hardware-token key wanted later? | passphrase now; token is a future change |
