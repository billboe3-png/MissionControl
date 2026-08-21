"""Mission Control Edge Agent - Windows Service Wrapper."""
from __future__ import annotations

import os
import subprocess
import sys

sys.path.insert(0, r'C:\MissionControlAgent')

import win32event
import win32service
import win32serviceutil


class EdgeAgentService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MissionControlEdgeAgent"
    _svc_display_name_ = "Mission Control Edge Agent"
    _svc_description_ = "Mission Control offline-first edge collector agent."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass

    def SvcRun(self):
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        cmd = [r'C:\Users\robert\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe', '-m', 'agent']
        cwd = r'C:\MissionControlAgent'
        env = dict(os.environ)
        env.update({
            'MC_SERVER_URL': 'https://missioncontrol.optichosting.co.za',
            'MC_API_KEY': 'mc_agent_cd1a4b965593a04b05a4a919e0878222b8db924514a403a4f4129db59f2bb796',
            'MC_AGENT_ID': '1',
        })
        while True:
            self.process = subprocess.Popen(cmd, cwd=cwd, env=env, creationflags=subprocess.CREATE_NO_WINDOW)
            rc = win32event.WaitForSingleObject(self.stop_event, 5000)
            if rc == win32event.WAIT_OBJECT_0:
                try:
                    self.process.terminate()
                except Exception:
                    pass
                break
            if self.process.poll() is not None:
                pass


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(EdgeAgentService)
