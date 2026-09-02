import { useState, useEffect } from "react";
import PageHeader from "../../components/common/PageHeader";
import { mikrotikApi, MikroTikServer } from "../../services/mikrotik";

type Tab = "interfaces" | "ip-addresses" | "firewall" | "dhcp" | "system";

export default function MikroTikConfigPage() {
  const [servers, setServers] = useState<MikroTikServer[]>([]);
  const [serverId, setServerId] = useState<number | null>(null);
  const [tab, setTab] = useState<Tab>("interfaces");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [interfaces, setInterfaces] = useState<any[]>([]);
  const [ipAddresses, setIpAddresses] = useState<any[]>([]);
  const [firewallRules, setFirewallRules] = useState<any[]>([]);
  const [dhcpLeases, setDhcpLeases] = useState<any[]>([]);
  const [systemConfig, setSystemConfig] = useState<any>({});

  const loadServers = () => {
    setLoading(true);
    mikrotikApi
      .listServers()
      .then((items) => {
        setServers(items);
        if (!serverId && items.length > 0) {
          setServerId(items[0].id);
        }
      })
      .catch(() => setError("Failed to load servers"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadServers();
  }, []);

  useEffect(() => {
    if (serverId == null) return;
    setLoading(true);
    setError(null);
    setSuccess(null);
    (async () => {
      try {
        switch (tab) {
          case "interfaces": {
            const res = await mikrotikApi.listInterfacesConfig(serverId);
            setInterfaces(res.interfaces || []);
            break;
          }
          case "ip-addresses": {
            const res = await mikrotikApi.listConfigIpAddresses(serverId);
            setIpAddresses(res.addresses || []);
            break;
          }
          case "firewall": {
            const res = await mikrotikApi.listFirewallRulesConfig(serverId);
            setFirewallRules(res.rules || []);
            break;
          }
          case "dhcp": {
            const res = await mikrotikApi.listDhcpLeasesConfig(serverId);
            setDhcpLeases(res.leases || []);
            break;
          }
          case "system": {
            const res = await mikrotikApi.getSystemConfig(serverId);
            setSystemConfig(res.config || {});
            break;
          }
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    })();
  }, [serverId, tab]);

  const currentServer = servers.find((s) => s.id === serverId) || null;

  const handleUpdateInterface = async (name: string, updates: any) => {
    if (!serverId) return;
    setSaving(true);
    setError(null);
    try {
      await mikrotikApi.updateInterface(serverId, name, updates);
      setSuccess("Interface updated");
      setTab("interfaces");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    } finally {
      setSaving(false);
    }
  };

  const handleCreateIpAddress = async (payload: any) => {
    if (!serverId) return;
    setSaving(true);
    setError(null);
    try {
      await mikrotikApi.createIpAddress(serverId, payload);
      setSuccess("IP address added");
      setTab("ip-addresses");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Create failed");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteIpAddress = async (id: string) => {
    if (!serverId) return;
    setSaving(true);
    setError(null);
    try {
      await mikrotikApi.deleteIpAddress(serverId, id);
      setSuccess("IP address removed");
      setTab("ip-addresses");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateSystem = async (payload: any) => {
    if (!serverId) return;
    setSaving(true);
    setError(null);
    try {
      await mikrotikApi.updateSystemConfig(serverId, payload);
      setSuccess("System config updated");
      setTab("system");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    } finally {
      setSaving(false);
    }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: "interfaces", label: "Interfaces" },
    { id: "ip-addresses", label: "IP Addresses" },
    { id: "firewall", label: "Firewall" },
    { id: "dhcp", label: "DHCP" },
    { id: "system", label: "System" },
  ];

  return (
    <div>
      <PageHeader title="MikroTik Config" subtitle="Native RouterOS configuration" />
      <div style={{ marginBottom: 12, display: "flex", gap: 12, alignItems: "center" }}>
        <label>
          Server{" "}
          <select
            value={serverId ?? ""}
            onChange={(e) => setServerId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">Select server</option>
            {servers.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.host})
              </option>
            ))}
          </select>
        </label>
        <div style={{ display: "flex", gap: 8 }}>
          {tabs.map((t) => (
            <button
              key={t.id}
              className={`btn ${tab === t.id ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="error-banner" style={{ marginBottom: 12 }}>{error}</div>}
      {success && <div className="success-banner" style={{ marginBottom: 12 }}>{success}</div>}

      <div className="card">
        <div className="card-header">
          <div className="card-title">{currentServer ? `${currentServer.name} — ${tabs.find((t) => t.id === tab)?.label}` : tabs.find((t) => t.id === tab)?.label}</div>
        </div>
        <div className="card-body">
          {loading ? (
            <div className="loading-bar">Loading...</div>
          ) : serverId == null ? (
            <div className="empty-state">Select a server to manage its configuration.</div>
          ) : (
            <ConfigTab
              tab={tab}
              server={currentServer}
              interfaces={interfaces}
              ipAddresses={ipAddresses}
              firewallRules={firewallRules}
              dhcpLeases={dhcpLeases}
              systemConfig={systemConfig}
              saving={saving}
              onUpdateInterface={handleUpdateInterface}
              onCreateIpAddress={handleCreateIpAddress}
              onDeleteIpAddress={handleDeleteIpAddress}
              onUpdateSystem={handleUpdateSystem}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function ConfigTab({
  tab,
  server,
  interfaces,
  ipAddresses,
  firewallRules,
  dhcpLeases,
  systemConfig,
  saving,
  onUpdateInterface,
  onCreateIpAddress,
  onDeleteIpAddress,
  onUpdateSystem,
}: any) {
  if (tab === "interfaces") {
    return (
      <div className="grid gap-2">
        {interfaces.map((iface: any) => (
          <div key={iface.name} className="card" style={{ marginBottom: 8 }}>
            <div className="card-body">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <strong>{iface.name}</strong> <span className="muted">({iface.type})</span>
                  <div className="muted">
                    Status: {iface.status} | MTU: {iface.mtu} | MAC: {iface.mac || "—"}
                  </div>
                  {iface.comment && <div className="muted">Comment: {iface.comment}</div>}
                </div>
                <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <input
                    type="checkbox"
                    checked={!!iface.disabled}
                    onChange={async (e) => {
                      await onUpdateInterface(iface.name, { disabled: e.target.checked });
                    }}
                    disabled={saving}
                  />
                  <span>Disabled</span>
                </label>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (tab === "ip-addresses") {
    return (
      <div className="grid gap-2">
        {ipAddresses.map((addr: any) => (
          <div key={addr.id} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #eee" }}>
            <div>
              <strong>{addr.address}</strong> <span className="muted">on {addr.interface}</span>
              {addr.comment && <div className="muted">Comment: {addr.comment}</div>}
            </div>
            <button className="btn btn-sm btn-danger" disabled={saving} onClick={() => onDeleteIpAddress(addr.id)}>
              Remove
            </button>
          </div>
        ))}
        <IpForm serverId={server.id} saving={saving} onSubmit={onCreateIpAddress} />
      </div>
    );
  }

  if (tab === "firewall") {
    return (
      <div className="grid gap-2">
        {firewallRules.map((rule: any) => (
          <div key={rule.id} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #eee" }}>
            <div>
              <strong>#{rule.id}</strong> <span className="muted">{rule.chain}</span>
              <div>
                {rule.action} | {rule.protocol || "any"} | {rule.src_address} → {rule.dst_address}:{rule.dst_port}
              </div>
              {rule.comment && <div className="muted">Comment: {rule.comment}</div>}
            </div>
            <span className={`status-badge ${rule.disabled ? "status-disabled" : "status-ok"}`}>
              {rule.disabled ? "disabled" : "active"}
            </span>
          </div>
        ))}
      </div>
    );
  }

  if (tab === "dhcp") {
    return (
      <div className="grid gap-2">
        {dhcpLeases.map((lease: any) => (
          <div key={lease.id} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #eee" }}>
            <div>
              <strong>{lease.address}</strong> <span className="muted">{lease.mac_address}</span>
              <div className="muted">{lease.host_name || "—"} | {lease.status} | expires {lease.expires_after || "—"}</div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (tab === "system") {
    return (
      <div className="grid gap-2">
        <div className="form-row">
          <label>Identity</label>
          <input
            defaultValue={systemConfig.identity || ""}
            onBlur={async (e) => {
              const val = e.target.value.trim();
              if (val) {
                await onUpdateSystem({ identity: val });
              }
            }}
          />
        </div>
        {systemConfig.routerboard && (
          <div className="grid gap-1" style={{ marginTop: 8 }}>
            <strong>RouterBoard</strong>
            <div className="muted">{JSON.stringify(systemConfig.routerboard)}</div>
          </div>
        )}
      </div>
    );
  }

  return null;
}

function IpForm({ serverId, saving, onSubmit }: { serverId: number; saving: boolean; onSubmit: (payload: any) => Promise<void> }) {
  const [address, setAddress] = useState("");
  const [iface, setIface] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!address || !iface) return;
    await onSubmit({ address, interface: iface });
    setAddress("");
    setIface("");
  };

  return (
    <form onSubmit={submit} style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "center" }}>
      <input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="10.0.0.1/24" />
      <input value={iface} onChange={(e) => setIface(e.target.value)} placeholder="bridgeLocal" />
      <button className="btn btn-primary" type="submit" disabled={saving}>
        Add IP
      </button>
    </form>
  );
}
