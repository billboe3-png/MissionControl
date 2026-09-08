import { useState, useEffect } from "react";
import PageHeader from "../../components/common/PageHeader";
import { mikrotikApi, MikroTikServer, MikroTikFirewallRule } from "../../services/mikrotik";

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

export default function MikroTikFirewallPage() {
  const [servers, setServers] = useState<MikroTikServer[]>([]);
  const [serverId, setServerId] = useState<number | null>(null);
  const [rules, setRules] = useState<MikroTikFirewallRule[]>([]);
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
      .getFirewall(serverId)
      .then((res) => {
        if (!cancelled) {
          setRules(res.rules || []);
          setError(null);
        }
      })
      .catch(() => {
        if (!cancelled) setError("Failed to load firewall rules.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [serverId]);

  const filtered = rules.filter((rule) => {
    if (!search.trim()) return true;
    const needle = search.toLowerCase();
    return (
      rule.chain.toLowerCase().includes(needle) ||
      (rule.action || "").toLowerCase().includes(needle) ||
      (rule.comment || "").toLowerCase().includes(needle)
    );
  });

  return (
    <>
      <PageHeader title="MikroTik Firewall" subtitle="Filter rules with byte and packet counters" />

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
            placeholder="Search chain, action, comment…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ maxWidth: 280 }}
          />
        </div>
      )}

      {loading ? (
        <div className="loading-bar">Loading firewall rules…</div>
      ) : servers.length === 0 ? (
        <div className="empty-state">No MikroTik servers configured yet.</div>
      ) : (
        <>
          {error && <div className="error-banner" style={{ marginBottom: 12 }}>{error}</div>}
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Chain</th>
                  <th>Action</th>
                  <th>Comment</th>
                  <th>State</th>
                  <th>Bytes</th>
                  <th>Packets</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="empty-text">
                      {rules.length === 0 ? "No firewall rules available." : "No rules match the filter."}
                    </td>
                  </tr>
                ) : (
                  filtered.map((rule, idx) => (
                    <tr key={`${rule.chain}-${idx}`}>
                      <td>{rule.chain}</td>
                      <td>{rule.action || "—"}</td>
                      <td className="muted">{rule.comment || "—"}</td>
                      <td>
                        {rule.disabled ? (
                          <span className="status-badge status-disabled">disabled</span>
                        ) : (
                          <span className="status-badge status-healthy">active</span>
                        )}
                      </td>
                      <td>{formatBytes(rule.bytes)}</td>
                      <td>{rule.packets.toLocaleString()}</td>
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
