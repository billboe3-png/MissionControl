import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import { formatDateTime } from "../../utils/dateFormat";

type ServerStatus = {
  name: string;
  status: "online" | "offline" | "unknown";
  ip: string;
  version: string;
  uptime: string;
};

type ProxyStatus = {
  id: number;
  name: string;
  status: "online" | "offline" | "unknown";
  platform: string;
  ip: string;
  last_heartbeat: string;
  target_count: number;
};

type DatabaseStatus = {
  name: string;
  status: "online" | "offline" | "unknown";
  type: string;
  size: string;
};

type ComponentStatus = {
  servers: ServerStatus[];
  proxies: ProxyStatus[];
  databases: DatabaseStatus[];
  agents: number;
  targets: number;
  plugins: number;
};

export default function ZabbixOverviewPage() {
  const [data, setData] = useState<ComponentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([
      fetch("/api/v1/health/subsystems").then((r) => r.json()),
      fetch("/api/v1/agents").then((r) => r.json()),
    ])
      .then(([health, agentsRes]) => {
        if (cancelled) return;

        const servers: ServerStatus[] = [
          {
            name: "Mission Control Server",
            status: health?.status === "healthy" ? "online" : "unknown",
            ip: "34.35.177.209",
            version: health?.version || "3.0.0-rc1",
            uptime: health?.uptime || "—",
          },
        ];

        const proxies: ProxyStatus[] = (agentsRes.items ?? []).map((agent: any) => ({
          id: agent.id,
          name: agent.name ?? `Agent ${agent.id}`,
          status: agent.status === "online" ? "online" : "offline",
          platform: agent.operating_system || "unknown",
          ip: agent.ip_address || "—",
          last_heartbeat: agent.last_heartbeat || "—",
          target_count: 0,
        }));

        const databases: DatabaseStatus[] = [
          {
            name: "PostgreSQL",
            status: "online",
            type: "PostgreSQL",
            size: "—",
          },
        ];

        const totalTargets = proxies.reduce(
          (sum, p) => sum + p.target_count,
          0
        );

        setData({
          servers,
          proxies,
          databases,
          agents: proxies.length,
          targets: totalTargets,
          plugins: 0,
        });
        setLoading(false);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e.message);
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const renderStatus = (status: string) => {
    const color =
      status === "online"
        ? "#22c55e"
        : status === "offline"
        ? "#ef4444"
        : "#94a3b8";
    return (
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          color,
          fontWeight: 600,
        }}
      >
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            backgroundColor: color,
            display: "inline-block",
          }}
        />
        {status.toUpperCase()}
      </span>
    );
  };

  if (error) return <div className="error-banner">{error}</div>;
  if (loading) return <div className="loading-bar" />;
  if (!data) return null;

  return (
    <>
      <PageHeader
        title="Overview"
        subtitle="Mission Control architecture mirrors Zabbix Server/Proxy/Target topology"
      />

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16, marginBottom: 24 }}>
        <div className="card">
          <h3>Server</h3>
          <p style={{ fontSize: 13, color: "#64748b", marginBottom: 8 }}>
            Central component: configuration, data storage, API, and web UI.
          </p>
          {data.servers.map((s) => (
            <div key={s.name} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <strong>{s.name}</strong>
                {renderStatus(s.status)}
              </div>
              <div style={{ fontSize: 12, color: "#64748b" }}>
                IP: {s.ip} | Version: {s.version}
              </div>
              <div style={{ fontSize: 12, color: "#64748b" }}>
                Uptime: {s.uptime}
              </div>
            </div>
          ))}
        </div>

        <div className="card">
          <h3>Database Storage</h3>
          <p style={{ fontSize: 13, color: "#64748b", marginBottom: 8 }}>
            All configuration, historical metrics, and operational data.
          </p>
          {data.databases.map((db) => (
            <div key={db.name} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <strong>{db.name}</strong>
                {renderStatus(db.status)}
              </div>
              <div style={{ fontSize: 12, color: "#64748b" }}>
                Type: {db.type} | Size: {db.size}
              </div>
            </div>
          ))}
        </div>

        <div className="card">
          <h3>Web Interface</h3>
          <p style={{ fontSize: 13, color: "#64748b", marginBottom: 8 }}>
            React-based GUI for visualization, dashboards, and configuration.
          </p>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <strong>missioncontrol.optichosting.co.za</strong>
            {renderStatus("online")}
          </div>
          <div style={{ fontSize: 12, color: "#64748b" }}>
            Port: 443 | Protocol: HTTPS
          </div>
        </div>

        <div className="card">
          <h3>Proxies</h3>
          <p style={{ fontSize: 13, color: "#64748b", marginBottom: 8 }}>
            Edge agents collect data in remote locations and buffer offline.
          </p>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
            <strong>Total Proxies</strong>
            <span style={{ fontSize: 20, fontWeight: 700 }}>{data.proxies.length}</span>
          </div>
          {data.proxies.map((p) => (
            <div
              key={p.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: 12,
                color: "#64748b",
                borderTop: "1px solid #f1f5f9",
                paddingTop: 4,
                marginTop: 4,
              }}
            >
              <span>
                {p.name} ({p.platform})
              </span>
              {renderStatus(p.status)}
            </div>
          ))}
        </div>

        <div className="card">
          <h3>Agents / Targets</h3>
          <p style={{ fontSize: 13, color: "#64748b", marginBottom: 8 }}>
            Lightweight monitoring via SSH, REST, or agentless protocols.
          </p>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span>Agents</span>
            <strong>{data.agents}</strong>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span>Targets</span>
            <strong>{data.targets}</strong>
          </div>
        </div>

        <div className="card">
          <h3>Data Flow</h3>
          <p style={{ fontSize: 13, color: "#64748b", marginBottom: 8 }}>
            Passive checks: targets respond to proxy collection. Active checks:
            proxies auto-discover and push data. Agentless: SSH/REST/SNMP/WMI.
          </p>
          <div style={{ fontSize: 12, color: "#64748b", fontFamily: "monospace" }}>
            [Targets] → [Proxy] → [Server] → [Database] → [Web UI]
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Proxy Details</h3>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #e2e8f0", textAlign: "left" }}>
              <th style={{ padding: 8 }}>ID</th>
              <th style={{ padding: 8 }}>Name</th>
              <th style={{ padding: 8 }}>Platform</th>
              <th style={{ padding: 8 }}>IP</th>
              <th style={{ padding: 8 }}>Status</th>
              <th style={{ padding: 8 }}>Last Heartbeat</th>
              <th style={{ padding: 8 }}>Targets</th>
            </tr>
          </thead>
          <tbody>
            {data.proxies.map((p) => (
              <tr key={p.id} style={{ borderBottom: "1px solid #f1f5f0" }}>
                <td style={{ padding: 8 }}>{p.id}</td>
                <td style={{ padding: 8 }}>{p.name}</td>
                <td style={{ padding: 8 }}>{p.platform}</td>
                <td style={{ padding: 8 }}>{p.ip}</td>
                <td style={{ padding: 8 }}>{renderStatus(p.status)}</td>
                <td style={{ padding: 8 }}>
                  {p.last_heartbeat !== "—"
                    ? formatDateTime(p.last_heartbeat)
                    : "—"}
                </td>
                <td style={{ padding: 8 }}>{p.target_count}</td>
              </tr>
            ))}
            {data.proxies.length === 0 && (
              <tr>
                <td colSpan={7} style={{ padding: 12, textAlign: "center", color: "#64748b" }}>
                  No proxies deployed yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
