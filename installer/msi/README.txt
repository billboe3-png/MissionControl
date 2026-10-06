Mission Control Edge Agent — Install notes

The agent runs as a SYSTEM scheduled task (MissionControlEdgeAgent) using a
dedicated Python virtualenv at C:\MissionControlAgent\venv. It polls
https://missioncontrol.optichosting.co.za, heartbeats, and executes commands.

  Config    : C:\MissionControlAgent\config.yaml
  Install log : C:\MissionControlAgent\install.log (installer transcript)
  Task      : MissionControlEdgeAgent
  Stop      : Stop-ScheduledTask -TaskName MissionControlEdgeAgent
  Start     : Start-ScheduledTask -TaskName MissionControlEdgeAgent

Reinstall: run the MSI again; the previous install is superseded.
Uninstall: Add/Remove Programs -> "Mission Control Edge Agent", or
           msiexec /x MissionControlEdgeAgent-3.0.0-rc1.msi /qn
Uninstall removes the scheduled task, agent processes, and
C:\MissionControlAgent. Python itself is not removed.