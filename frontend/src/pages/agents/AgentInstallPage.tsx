'use client';

import { useState } from "react";
import PageHeader from "../../components/common/PageHeader";

type Platform = "windows" | "linux";

const STEPS: Record<Platform, string[]> = {
  windows: [
    "Download the **Windows installer** using the button below and save it to your **Downloads** folder.",
    "Right-click the downloaded `.bat` file and choose **Run as administrator**.",
    "The installer will download the agent package, create the configuration, and register a scheduled task. When it says **Installation complete**, close the window.",
    "Verify by opening **Task Scheduler** (`taskschd.msc`) and confirming `MissionControlAgent` is present and last ran successfully.",
    "Return to this page. The new agent should appear in the agents list within 1 to 2 minutes. If it does not appear, refresh the page.",
  ],
  linux: [
    "Download the **Linux bundle** using the button below and save it.",
    "Transfer the ZIP to the Linux machine using SCP, WinSCP, sshfs, or USB.",
    "Open a terminal on the Linux machine and extract: `sudo unzip /path/to/mission-control-agent-linux-bundle.zip -d /opt/mission-control-agent`",
    "Create the config file: `sudo nano /opt/mission-control-agent/agent/config.yaml` and paste your agent API key, then save and exit.",
    "Set up Python and dependencies: `cd /opt/mission-control-agent && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`",
    "Test manually: `python3 -m agent`. Leave this terminal open for a moment. You should see heartbeat messages. Press Ctrl+C to stop the manual test.",
    "Install as a service so it starts automatically using systemd or your preferred init system.",
  ],
};

export default function AgentInstallPage() {
  const [platform, setPlatform] = useState<Platform>("windows");
  const [downloading, setDownloading] = useState<string | null>(null);

  const download = async (name: string, url: string) => {
    setDownloading(name);
    try {
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div style={{ maxWidth: 860, margin: "0 auto" }}>
      <PageHeader title="Install Agent" subtitle="Deploy the Mission Control Agent on your infrastructure" />

      <div className="card" style={{ padding: 16, marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            className={`btn ${platform === "windows" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setPlatform("windows")}
          >
            Windows
          </button>
          <button
            className={`btn ${platform === "linux" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setPlatform("linux")}
          >
            Linux
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 16 }}>
        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontWeight: 700, marginBottom: 12 }}>Download</div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button
              className="btn btn-primary"
              disabled={downloading === "windows"}
              onClick={() =>
                download(
                  "install-agent.bat",
                  "/api/v1/agents/debug/install-agent.bat",
                )
              }
            >
              {downloading === "windows" ? "Preparing…" : "Download Windows installer"}
            </button>
            <button
              className="btn btn-primary"
              disabled={downloading === "linux"}
              onClick={() =>
                download(
                  "mission-control-agent-linux-bundle.zip",
                  "/api/v1/agents/bundles/download",
                )
              }
            >
              {downloading === "linux" ? "Preparing…" : "Download Linux bundle"}
            </button>
          </div>
          <div style={{ marginTop: 10, fontSize: 12, color: "#94a3b8" }}>
            If the download does not start, copy the URL and paste it into a new browser tab.
          </div>
        </div>

        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontWeight: 700, marginBottom: 12 }}>
            {platform === "windows" ? "Windows installation" : "Linux installation"}
          </div>
          <ol style={{ margin: 0, paddingLeft: 18, lineHeight: 1.7 }}>
            {STEPS[platform].map((step, idx) => (
              <li key={idx} style={{ marginBottom: 6 }}>{step}</li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}
