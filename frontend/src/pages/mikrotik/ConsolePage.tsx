import { useState, useEffect } from "react";
import PageHeader from "../../components/common/PageHeader";
import { mikrotikApi, MikroTikServer } from "../../services/mikrotik";

const QUICK_COMMANDS = [
  "/system resource print",
  "/interface print",
  "/ip address print",
  "/ip route print",
  "/system logging print",
];

export default function MikroTikConsolePage() {
  const [servers, setServers] = useState<MikroTikServer[]>([]);
  const [serverId, setServerId] = useState<number | null>(null);
  const [command, setCommand] = useState("");
  const [useTelnet, setUseTelnet] = useState(false);
  const [output, setOutput] = useState<string>("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    mikrotikApi
      .listServers()
      .then((items) => {
        setServers(items);
        setServerId(items.find((s) => s.enabled)?.id ?? items[0]?.id ?? null);
      })
      .catch(() => setError("Failed to load MikroTik servers."));
  }, []);

  const run = async (cmd?: string) => {
    if (serverId == null) return;
    const target = (cmd ?? command).trim();
    if (!target) return;
    setRunning(true);
    setError(null);
    try {
      const res = await mikrotikApi.executeCommand(serverId, target, useTelnet);
      setOutput(
        (prev) =>
          `${prev}${prev ? "\n" : ""}[${new Date().toLocaleTimeString()}] ${target}\n${
            res.success ? res.output : `ERROR: ${res.output}`
          }`
      );
    } catch {
      setError("Command execution failed.");
    } finally {
      setRunning(false);
    }
  };

  return (
    <>
      <PageHeader title="MikroTik Console" subtitle="Run RouterOS commands over SSH or Telnet" />

      {servers.length > 0 && (
        <div className="card" style={{ marginBottom: 12 }}>
          <div className="card-body">
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
              <select
                className="form-input"
                value={serverId ?? ""}
                onChange={(e) => setServerId(Number(e.target.value))}
                style={{ maxWidth: 320 }}
              >
                {servers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.host})
                  </option>
                ))}
              </select>
              <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <input type="checkbox" checked={useTelnet} onChange={(e) => setUseTelnet(e.target.checked)} />
                <span>Telnet</span>
              </label>
            </div>
            <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
              <input
                className="form-input"
                style={{ flex: 1 }}
                value={command}
                placeholder="/system resource print"
                onChange={(e) => setCommand(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !running) void run();
                }}
              />
              <button className="btn btn-primary" disabled={running || !command.trim()} onClick={() => void run()}>
                {running ? "Running…" : "Run"}
              </button>
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
              {QUICK_COMMANDS.map((cmd) => (
                <button
                  key={cmd}
                  className="btn"
                  onClick={() => void run(cmd)}
                  disabled={running}
                >
                  {cmd}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {error && <div className="error-banner" style={{ marginBottom: 12 }}>{error}</div>}

      {output ? (
        <div className="card">
          <div className="card-header">
            <div className="card-title">Output</div>
            <button className="btn" onClick={() => setOutput("")}>
              Clear
            </button>
          </div>
          <div className="card-body">
            <pre
              style={{
                margin: 0,
                maxHeight: 480,
                overflow: "auto",
                whiteSpace: "pre-wrap",
                fontFamily: "monospace",
                fontSize: 13,
              }}
            >
              {output}
            </pre>
          </div>
        </div>
      ) : (
        servers.length === 0 && <div className="empty-state">No MikroTik servers configured yet.</div>
      )}
    </>
  );
}
