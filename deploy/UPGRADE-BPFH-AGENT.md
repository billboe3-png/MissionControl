# Upgrade bpfhb-zabbix-proxy agent (BPFHBDC01 Veeam relay)

**Why:** The agent on `bpfhb-zabbix-proxy` (192.168.4.29) runs an older build whose
`edge_core.py` lacks the `namespace == "veeam"` dispatch. Every `veeam:*` relay
from the backend returns `No target_id specified for remote_execute`, so the
BPFHBDC01 Veeam server syncs nothing.

**Fix:** Re-run the Linux installer so it pulls the freshly built live bundle
(`agent-bundle-live.zip`, v0.0.1) whose edge code dispatches `veeam` / `active_directory`
namespaces to the plugin manager.

## Prep (done on GCP server, 2026-09-01)

- Built `/opt/MissionControl/.agents/agent-bundle-live.zip` (v0.0.1) from the
  current `.agents/agent/` package (includes `edge_core.py` veeam dispatch and
  `plugins/veeam_plugin.py`).
- Verified the backend serves it (inside `missioncontrol-backend-1`):
  - `GET/POST /api/v1/agents/8/bundles/download` -> 200 `application/zip` (399089 bytes)
  - edge: `/api/v1/edge/8/bundle/download` -> 200

## Runbook

Run on the BPFH box (`bpfhb-zabbix-proxy`, 192.168.4.29), as **root**:

```bash
# 1. Confirm current install layout
systemctl status mission-control-agent --no-pager | head -10
ls -la /opt/mission-control-agent/ | head        # contains config.yaml, venv, agent/
grep -n 'api_key' /opt/mission-control-agent/config.yaml   # grab the key from here

# 2. Copy the Linux installer to the box (from GCP server /opt/MissionControl/.agents/install-agent-linux.sh)
#    e.g. scp install-agent-linux.sh root@192.168.4.29:/root/

# 3. Re-run the installer with the SAME agent id and API key (picks up the new bundle)
sudo ./install-agent-linux.sh \
  --server https://missioncontrol.optichosting.co.za \
  --agent-id 8 \
  --api-key <API_KEY-from-config.yaml>
```

The installer re-downloads the live bundle, re-extracts `agent/`, reuses/rebuilds
`venv/`, rewrites an identical `config.yaml`, and restarts the systemd service.

## Verify

On the BPFH box:

```bash
systemctl is-active mission-control-agent        # expect: active
journalctl -u mission-control-agent -n 30 --no-pager
```

From the GCP server (I can run this): backend now routes server 12's relays
through the upgraded agent. Confirm `VeeamBackupServer` id 12 job count > 0 and
`/api/v1/plugins/veeam/overview` lists jobs for both servers.

If the DB-collect path for MSSQL (VeeamBackup.mdf via SQLCMD on target 12) needs
verification, run the `test_bpfh.py` provider script against server 12 and check
`get_jobs()` returns the BPFH job list.