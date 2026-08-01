'use client';

type Props = {
  variant?: 'default' | 'compact';
};

const WINDOWS_STEPS = [
  'Download the **Windows installer** using the button below and save it to your **Downloads** folder.',
  'Open **File Explorer**, go to **Downloads**, right-click the downloaded `.bat` file, and choose **Edit**. Update the `AgentId` and `ApiKey` values near the top of the file, then save.',
  'Right-click the saved `.bat` file and choose **Run as administrator**. If a permission popup appears, click **Yes**.',
  'The installer will download the agent package, create the configuration, and register a scheduled task. When it says **Installation complete**, close the window.',
  'Verify by opening **Task Scheduler** (`taskschd.msc`) and confirming `MissionControlAgent` is present and last ran successfully.',
  'Return to this Mission Control page. The new agent should appear in the agents list within 1 to 2 minutes. If it does not appear, refresh the page.',
];

const LINUX_STEPS = [
  'Download the Linux bundle ZIP using the **Download Linux bundle** button on the Agents page and save it.',
  'Transfer the ZIP to the Linux machine using SCP, WinSCP, sshfs, or USB.',
  'Open a terminal on the Linux machine and extract: `sudo unzip /path/to/mission-control-agent-linux-bundle.zip -d /opt/mission-control-agent`',
  'Create the config file: `sudo nano /opt/mission-control-agent/agent/config.yaml` and paste your agent API key, then save and exit.',
  'Set up Python and dependencies: `cd /opt/mission-control-agent && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`',
  'Test manually: `python3 -m agent`. Leave this terminal open for a moment. You should see heartbeat messages. Press Ctrl+C to stop the manual test.',
  'Install as a service so it starts automatically using systemd or your preferred init system.',
];

export default function AgentInstallHelp({ variant = 'default' }: Props) {
  if (variant === 'compact') {
    return (
      <div className="card" style={{ padding: 12 }}>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Need install steps?</div>
        <div style={{ fontSize: 13, opacity: 0.9 }}>
          Windows: download the installer from the Agents page, edit the AgentId and ApiKey in the file, then run it as administrator.
          Linux: download the Linux bundle, extract to `/opt/mission-control-agent`, create config, activate venv, and start the agent service.
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ fontWeight: 700, marginBottom: 8 }}>Agent installation</div>
      <div style={{ display: 'grid', gap: 14 }}>
        <div>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Windows</div>
          <ol style={{ margin: 0, paddingLeft: 18 }}>
            {WINDOWS_STEPS.map((s, idx) => (
              <li key={idx} style={{ marginBottom: 4 }}>{s}</li>
            ))}
          </ol>
          <div style={{ marginTop: 8, fontSize: 12, opacity: 0.85 }}>
            Verify with Task Scheduler or the Mission Control agents page.
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
