import { useState, useEffect } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { mikrotikApi, MikroTikServer, MikroTikInterface } from "../../services/mikrotik";

export default function MikroTikOverviewPage() {
  const [servers, setServers] = useState<MikroTikServer[]>([]);
  const [interfaces, setInterfaces] = useState<Record<number, MikroTikInterface[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    mikrotikApi.listServers().then((items) => {
      if (cancelled) return;
      setServers(items);
      Promise.all(
        items
          .filter((s) => s.enabled)
          .map((server) =>
            mikrotikApi
              .getInterfaces(server.id)
              .then((res) => ({ serverId: server.id, interfaces: res.interfaces }))
              .catch(() => ({ serverId: server.id, interfaces: [] }))
          )
      ).then((results) => {
        if (cancelled) return;
        const map: Record<number, MikroTikInterface[]> = {};
        for (const item of results) {
          map[item.serverId] = item.interfaces;
        }
        setInterfaces(map);
      }).finally(() => {
        if (!cancelled) setLoading(false);
      });
    }).catch(() => setLoading(false));
    return () => { cancelled = true; };
  }, []);

  return (
    <>
      <PageHeader title="MikroTik" subtitle="RouterOS access: SSH, Telnet, and WebFig proxy" />

      {loading ? (
        <div className="loading-bar">Loading MikroTik servers…</div>
      ) : servers.length === 0 ? (
        <div className="empty-state">No MikroTik servers configured yet.</div>
      ) : (
        <div className="grid gap-3">
          {servers.map((server) => (
            <div key={server.id} className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">{server.name}</div>
                  <div className="card-subtitle">
                    {server.host}:{server.ssh_port}
                    {server.telnet_enabled && server.telnet_port ? ` | Telnet: ${server.telnet_port}` : ""}
                    {server.api_enabled && server.api_port ? ` | API: ${server.api_port}` : ""}
                  </div>
                </div>
                <StatusBadge status={server.status} />
              </div>
              <div className="card-body">
                <div className="grid gap-2">
                  <div>
                    <strong>Version:</strong> {server.version || "—"}
                  </div>
                  <div>
                    <strong>Board:</strong> {server.board_name || "—"}
                  </div>
                  <div>
                    <strong>Uptime:</strong> {server.uptime || "—"}
                  </div>
                  <div>
                    <strong>CPU:</strong> {server.cpu_load || "—"}
                  </div>
                  {server.last_error && (
                    <div className="error-banner" style={{ marginTop: 8 }}>
                      {server.last_error}
                    </div>
                  )}
                </div>
                <div className="grid gap-1" style={{ marginTop: 12 }}>
                  <strong>Interfaces</strong>
                  {(interfaces[server.id] || []).length === 0 && (
                    <div className="empty-text">No cached interface data.</div>
                  )}
                  {(interfaces[server.id] || []).map((iface) => (
                    <div key={iface.name} style={{ display: "flex", gap: 12 }}>
                      <span>{iface.name}</span>
                      <StatusBadge status={iface.status || "unknown"} />
                      <span className="muted">
                        RX: {iface.rx_bytes} / TX: {iface.tx_bytes}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
