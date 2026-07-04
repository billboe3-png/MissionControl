# Mission Control

Mission Control is a personal productivity platform for senior IT professionals.

## Vision

One dashboard.

One workflow.

One place to manage everything.

## Planned Modules

- Dashboard
- Tasks
- Projects
- Notes
- Focus Mode
- Resume Me
- Parking Lot
- Microsoft 365
- Google Workspace
- Ticket System
- Zabbix
- AI Assistant

Current Status

Sprint 1 - Foundation

## Developer CLI

Run the Mission Control developer CLI with PowerShell 7+:

```powershell
./scripts/mc.ps1 help
./scripts/mc.ps1 status
./scripts/mc.ps1 version
./scripts/mc.ps1 init
```

Docker helpers:

```powershell
./scripts/mc.ps1 docker up
./scripts/mc.ps1 docker logs
./scripts/mc.ps1 docker down
```

Git helpers:

```powershell
./scripts/mc.ps1 git status
./scripts/mc.ps1 git commit "chore: update developer tooling"
```

Reserved for future sprints:

```powershell
./scripts/mc.ps1 sprint create 2
./scripts/mc.ps1 build
./scripts/mc.ps1 clean
./scripts/mc.ps1 lint
./scripts/mc.ps1 test
```
