# Mission Control Edge Agent — Windows MSI

A thin WiX v3.14 MSI that wraps the authoritative [install-agent.ps1](../install-agent.ps1) flow. It ships the installer/uninstaller scripts as payload and drives them through an **elevated (SYSTEM), non-impersonated** custom action, so the MSI never goes stale when the agent bundle changes — the bundle is downloaded from Mission Control at install time.

## Build

```powershell
cd installer/msi
.\build-msi.ps1
# -> output\MissionControlEdgeAgent-3.0.0-rc1.msi
```

The build script downloads a **portable WiX v3.14** into `$env:USERPROFILE\.cache\wix314` on first run — no .NET SDK or WiX install needed. Output and intermediate files land in `installer/msi/output` and `installer/msi/build` (both build artifacts, not committed).

## Silent install (enterprise / GPO / MDM)

```
msiexec /i MissionControlEdgeAgent-3.0.0-rc1.msi /qn ^
       SERVERURL=https://missioncontrol.optichosting.co.za ^
       AGENTNAME=PC-01
```

| Property             | Meaning                                                                  |
|----------------------|--------------------------------------------------------------------------|
| `SERVERURL`          | Mission Control server URL (default: `https://missioncontrol.optichosting.co.za`) |
| `AGENTNAME`          | Agent display name (defaults to the computer hostname)                   |
| `REGISTRATIONTOKEN`  | One-time token — **only** when re-installing a hostname that is already registered |
| `SKIPSSLVERIFY`      | `1` disables TLS verification (default `0`)                              |

A brand-new machine self-registers (no token). If the server rejects re-registration, the install fails and the MSI rolls back; supply a `REGISTRATIONTOKEN` and retry.

## What it does on install

1. Locates Python 3.12 (installs it silently via winget/python.org if absent)
2. Creates `C:\MissionControlAgent\venv` + installs agent deps (incl. pywin32, WMI)
3. Downloads the newest agent bundle from `SERVERURL/api/v1/agents/bundles/download`
4. Registers the machine with Mission Control (token → API key)
5. Writes `C:\MissionControlAgent\config.yaml`
6. Registers a SYSTEM scheduled task `MissionControlEdgeAgent` (starts at boot) and starts it

Install log: `C:\MissionControlAgent\install.log`.

## Uninstall

Full removal — removes the scheduled task, stops agent processes, deletes `C:\MissionControlAgent` (Python itself stays):

```
msiexec /x MissionControlEdgeAgent-3.0.0-rc1.msi /qn
```

## Upgrade / reinstall

Re-running the MSI over an existing install is supported: `MajorUpgrade` supersedes the prior product, and `install-agent.ps1` stops the old task, reuses/refreshes the venv, and re-registers (token required only if the hostname is already registered).

## Files

| File                  | Purpose                                            |
|-----------------------|----------------------------------------------------|
| `agent.wxs`           | WiX v3.14 source (product, props, custom actions)  |
| `install-agent.ps1`   | Authoritative agent installer (payload)            |
| `uninstall-agent.ps1` | Agent uninstaller (payload)                        |
| `build-msi.ps1`       | Portable-WiX build script                          |
| `README.md`           | This file                                          |