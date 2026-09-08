import { useState, useEffect } from "react";
import PageHeader from "../../components/common/PageHeader";
import { mikrotikApi, MikroTikServer, MikroTikDhcpLease } from "../../services/mikrotik";

export default function MikroTikDhcpPage() {
  const [servers, setServers] = useState<MikroTikServer[]>([]);
  const [serverId, setServerId] = useState<number | null>(null);
  const [leases, setLeases] = useState<MikroTikDhcpLease[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    setLoading(true);
    mikrotikApi
      .listServers()
      .then((items) => {
        setServers(items);
        setServerId(items.find((s) => s.enabled)?.id ?? items[0]?.id ?? null);
      })
      .catch(() => setError("Failed to load MikroTik servers."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (serverId == null) return;
    let cancelled = false;
    setLoading(true);
    mikrotikApi
      .getDhcp(serverId)
      .then((res) => {
        if (!cancelled) {
          setLeases(res.leases || []);
          setError(null);
        }
      })
      .catch(() => {
        if (!cancelled) setError("Failed to load DHCP leases.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [serverId]);

  const filtered = leases.filter((lease) => {
    if (!search.trim()) return true;
    const needle = search.toLowerCase();
    return (
      (lease.address || "").toLowerCase().includes(needle) ||
      lease.mac.toLowerCase().includes(needle) ||
      (lease.host_name || "").toLowerCase().includes(needle)
    );
  });

  return (
    <>
      <PageHeader title="MikroTik DHCP" subtitle="DHCP server leases" />

      {servers.length > 0 && (
        <div style={{ marginBottom: 12, display: "flex", gap: 10 }}>
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
          <input
            className="form-input"
            type="search"
            placeholder="Search address, MAC, hostname…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ maxWidth: 280 }}
          />
        </div>
      )}

      {loading ? (
        <div className="loading-bar">Loading DHCP leases…</div>
      ) : servers.length === 0 ? (
        <div className="empty-state">No MikroTik servers configured yet.</div>
      ) : (
        <>
          {error && <div className="error-banner" style={{ marginBottom: 12 }}>{error}</div>}
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Address</th>
                  <th>MAC</th>
                  <th>Hostname</th>
                  <th>Status</th>
                  <th>Expires</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="empty-text">
                      {leases.length === 0 ? "No DHCP leases available." : "No leases match the filter."}
                    </td>
                  </tr>
                ) : (
                  filtered.map((lease, idx) => (
                    <tr key={`${lease.mac}-${idx}`}>
                      <td>{lease.address || "—"}</td>
                      <td>{lease.mac}</td>
                      <td>{lease.host_name || "—"}</td>
                      <td>
                        <span
                          className={`status-badge ${
                            lease.status === "bound" ? "status-healthy" : "status-disabled"
                          }`}
                        >
                          {lease.status || "unknown"}
                        </span>
                      </td>
                      <td>{lease.expires || "—"}</td>
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
