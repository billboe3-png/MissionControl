import { useState, useEffect } from "react";
import PageHeader from "../../components/common/PageHeader";
import { mikrotikApi, MikroTikServer, MikroTikInterface } from "../../services/mikrotik";

function formatBytes(n: number): string {
  if (!n && n !== 0) return "—";
  const units = ["B", "KiB", "MiB", "GiB", "TiB"];
  let value = n;
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i += 1;
  }
  return `${value.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

export default function MikroTikInterfacesPage() {
  const [servers, setServers] = useState<MikroTikServer[]>([]);
  const [serverId, setServerId] = useState<number | null>(null);
  const [interfaces, setInterfaces] = useState<MikroTikInterface[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadServers = () => {
    setLoading(true);
    mikrotikApi
      .listServers()
      .then((items) => {
        setServers(items);
        setServerId((prev) => prev ?? items.find((s) => s.enabled)?.id ?? items[0]?.id ?? null);
      })
      .catch(() => setError("Failed to load MikroTik servers."))
      .finally(() => setLoading(false));
  };

  useEffect(loadServers, []);

  useEffect(() => {
    if (serverId == null) return;
    let cancelled = false;
    const loadInterfaces = () => {
      mikrotikApi
        .getInterfaces(serverId)
        .then((res) => {
          if (!cancelled) {
            setInterfaces(res.interfaces || []);
            setError(null);
          }
        })
        .catch(() => {
          if (!cancelled) setError("Failed to load interface data.");
        });
    };
    loadInterfaces();
    const timer = window.setInterval(loadInterfaces, 30000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [serverId]);

  return (
    <>
      <PageHeader title="MikroTik Interfaces" subtitle="Live and cached interface status" />

      {servers.length > 0 && (
        <div style={{ marginBottom: 12 }}>
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
        </div>
      )}

      {loading ? (
        <div className="loading-bar">Loading interfaces…</div>
      ) : servers.length === 0 ? (
        <div className="empty-state">No MikroTik servers configured yet.</div>
      ) : (
        <>
          {error && <div className="error-banner" style={{ marginBottom: 12 }}>{error}</div>}
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Link</th>
                  <th>MAC</th>
                  <th>MTU</th>
                  <th>RX</th>
                  <th>TX</th>
                </tr>
              </thead>
              <tbody>
                {interfaces.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="empty-text">No interface data available.</td>
                  </tr>
                ) : (
                  interfaces.map((iface) => (
                    <tr key={iface.name}>
                      <td>{iface.name}</td>
                      <td>{iface.type || "—"}</td>
                      <td>
                        <span
                          className={`status-badge ${
                            iface.status === "running" ? "status-healthy" : "status-disabled"
                          }`}
                        >
                          {iface.status || "unknown"}
                        </span>
                      </td>
                      <td>{iface.link_status || "—"}</td>
                      <td className="muted">{iface.mac || "—"}</td>
                      <td>{iface.mtu ?? "—"}</td>
                      <td>{formatBytes(iface.rx_bytes)} ({iface.rx_packets})</td>
                      <td>{formatBytes(iface.tx_bytes)} ({iface.tx_packets})</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}
