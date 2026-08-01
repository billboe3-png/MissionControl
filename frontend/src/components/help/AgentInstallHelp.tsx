'use client';

type Props = {
  variant?: 'default' | 'compact';
};

const WINDOWS_STEPS = [
  'Download the Windows bundle ZIP using the **Download Windows bundle** button on this page and save it to your **Downloads** folder.',
  'Open **File Explorer**, go to **Downloads**, right-click the ZIP file, and choose **Extract all…**. Change the destination to **C:\MissionControlAgent**, then click **Extract**.',
  'Click the **Start** button, type **PowerShell**, right-click **Windows PowerShell**, and choose **Run as administrator**. If a permission popup appears, click **Yes**.',
  'Copy and paste this exact command below in PowerShell exactly as shown, then press Enter. Use the exact server address and a name for this computer: `.\install-agent.ps1 -ServerUrl https://missioncontrol.optichosting.co.za -AgentName THIS_COMPUTER_NAME`',
  'After pasting the full command, press **Enter**. Wait for the script to finish. It will show progress and then return to the command prompt.',
  'Confirm installation by opening **Services**: press the **Start** button, type `services.msc`, and press **Enter**. Scroll to **MissionControlAgent** and confirm the status is **Running**.',
  'Return to this Mission Control page. The new agent should appear in the list within 1 to 2 minutes. If it does not appear, refresh the page.',
];

const LINUX_STEPS = [
  'Download the Linux bundle ZIP using the **Download Linux bundle** button on this page and save it.',
  'Transfer the ZIP to the Linux machine using SCP, WinSCP, sshfs, or by copying it to a USB stick.',
  'Open a terminal on the Linux machine and run this exact command to extract the bundle into `/opt/mission-control-agent`: `sudo unzip /path/to/mission-control-agent-linux-bundle.zip -d /opt/mission-control-agent`. Replace `/path/to/...` with the actual path to the ZIP file. If you are not sure where it is, try `~/Downloads/mission-control-agent-linux-bundle.zip`.',
  'Create the config file by running: `sudo nano /opt/mission-control-agent/agent/config.yaml`. Paste your Mission Control agent API key into this file in the format required by the agent, then save and exit nano by pressing Ctrl+O, Enter, and Ctrl+X.',
  'Set up Python and install dependencies by running: `cd /opt/mission-control-agent && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`',
  'Start the agent manually once to test it: `python3 -m agent`. Leave this terminal window open for a moment. You should see heartbeat messages. If it shows an error, check the config path and API key, then try again. Press Ctrl+C to stop the manual test when heartbeat messages appear.',
  'Install the agent as a service so it starts automatically using systemd or your preferred init system. Confirm the new agent appears in this page within 1 to 2 minutes, or refresh the page if needed.',
];

export default function AgentInstallHelp({ variant = 'default' }: Props) {
  if (variant === 'compact') {
    return (
      <div className="card" style={{ padding: 12 }}>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Need install steps?</div>
        <div style={{ fontSize: 13, opacity: 0.9 }}>
          Windows: download the Windows bundle, extract to `C:\MissionControlAgent`, open PowerShell as administrator, then run `.\install-agent.ps1 -ServerUrl https://missioncontrol.optichosting.co.za -AgentName THIS_COMPUTER_NAME`.
          Linux: download the Linux bundle, extract to `/opt/mission-control-agent`, create config, activate venv, and start the agent service.
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ fontWeight: 700, marginBottom: 8 }}>Agent installation instructions</div>
      <div style={{ display: 'grid', gap: 14 }}>
        <div>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Windows</div>
          <ol style={{ margin: 0, paddingLeft: 18 }}>
            {WINDOWS_STEPS.map((s, idx) => (
              <li key={idx} style={{ marginBottom: 4 }}>{s}</li>
            ))}
          </ol>
          <div style={{ marginTop: 8, fontSize: 12, opacity: 0.85 }}>
            Verify with `Get-Service MissionControlAgent` or the **services.msc** app, then check the Mission Control agents page.
          </div>
        </div>
        <div>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Linux</div>
          <ol style={{ margin: 0, paddingLeft: 18 }}>
            {LINUX_STEPS.map((s, idx) => (
              <li key={idx} style={{ marginBottom: 4 }}>{s}</li>
            ))}
          </ol>
          <div style={{ marginTop: 8, fontSize: 12, opacity: 0.85 }}>
            Verify with `journalctl -u mission-control-agent` or the Mission Control agents page.
          </div>
        </div>
      </div>
    </div>
  );
}
