import { useState, useEffect } from "react";
import PageHeader from "../../components/common/PageHeader";
import {
  mikrotikApi,
  MikroTikServer,
  MikroTikInterface,
  MikroTikAgentOption,
} from "../../services/mikrotik";

interface FormState {
  name: string;
  host: string;
  ssh_port: number;
  username: string;
  password: string;
  enabled: boolean;
  telnet_enabled: boolean;
  telnet_port: number;
  api_enabled: boolean;
  api_port: number;
  relay_agent_id: number | null;
}

const EMPTY_FORM: FormState = {
  name: "",
  host: "",
  ssh_port: 22,
  username: "",
  password: "",
  enabled: true,
  telnet_enabled: false,
  telnet_port: 23,
  api_enabled: false,
  api_port: 443,
  relay_agent_id: null,
};

export default function MikroTikOverviewPage() {
  const [servers, setServers] = useState<MikroTikServer[]>([]);
  const [interfaces, setInterfaces] = useState<Record<number, MikroTikInterface[]>>({});
  const [ifaceErrors, setIfaceErrors] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [agents, setAgents] = useState<MikroTikAgentOption[]>([]);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [testingId, setTestingId] = useState<number | null>(null);
  const [testResult, setTestResult] = useState<string | null>(null);

  const loadInterfaces = (items: MikroTikServer[]) => {
    Promise.all(
      items
        .filter((s) => s.enabled)
        .map((server) =>
          mikrotikApi
            .getInterfaces(server.id)
            .then((res) => ({ serverId: server.id, interfaces: res.interfaces, error: "" }))
            .catch(
              () => ({
                serverId: server.id,
                interfaces: [],
                error: "Could not load interfaces (device unreachable or busy)",
              })
            )
        )
    ).then((results) => {
      const map: Record<number, MikroTikInterface[]> = {};
      const errors: Record<number, string> = {};
      for (const item of results) {
        map[item.serverId] = item.interfaces;
        if (item.error) errors[item.serverId] = item.error;
      }
      setInterfaces(map);
      setIfaceErrors(errors);
    });
  };

  const loadServers = () => {
    setLoading(true);
    mikrotikApi
      .listServers()
      .then((items) => {
        setServers(items);
        loadInterfaces(items);
      })
      .catch(() => undefined)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadServers();
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setServers((current) => {
        if (current.length > 0 && !showForm) loadInterfaces(current);
        return current;
      });
    }, 60000);
    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showForm]);

  const openCreate = async () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setShowForm(true);
    try {
      setAgents(await mikrotikApi.listAgents());
    } catch {
      setAgents([]);
    }
  };

  const openEdit = async (server: MikroTikServer) => {
    setEditingId(server.id);
    setForm({
      name: server.name,
      host: server.host,
      ssh_port: server.ssh_port || 22,
      username: server.username,
      password: "",
      enabled: server.enabled,
      telnet_enabled: server.telnet_enabled,
      telnet_port: server.telnet_port ?? 23,
      api_enabled: server.api_enabled,
      api_port: server.api_port ?? 443,
      // remote_target_id is not exposed in the list payload; refetch not needed here
      relay_agent_id: null,
    });
    try {
      const [agentList, detail] = await Promise.all([
        mikrotikApi.listAgents(),
        mikrotikApi.getServer(server.id),
      ]);
      setAgents(agentList);
      setForm((f) => ({ ...f, relay_agent_id: detail.relay_agent_id ?? null }));
    } catch {
      setAgents([]);
    }
    setFormError(null);
    setShowForm(true);
  };

  const handleSave = async () => {
    if (!form.name.trim() || !form.host.trim() || !form.username.trim()) {
      setFormError("Name, host, and username are required");
      return;
    }
    if (!editingId && !form.password) {
      setFormError("Password is required for a new server");
      return;
    }
    const payload: Record<string, unknown> = {
      name: form.name.trim(),
      host: form.host.trim(),
      ssh_port: form.ssh_port,
      username: form.username.trim(),
      enabled: form.enabled,
      telnet_enabled: form.telnet_enabled,
      api_enabled: form.api_enabled,
      relay_agent_id: form.relay_agent_id,
    };
    if (form.password) payload.password = form.password;
    if (form.telnet_enabled) payload.telnet_port = form.telnet_port;
    if (form.api_enabled) payload.api_port = form.api_port;

    setSaving(true);
    setFormError(null);
    try {
      if (editingId != null) {
        await mikrotikApi.updateServer(editingId, payload);
      } else {
        await mikrotikApi.createServer(payload);
      }
      setShowForm(false);
      setEditingId(null);
      setForm(EMPTY_FORM);
      loadServers();
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async (server: MikroTikServer) => {
    setTestingId(server.id);
    setTestResult(null);
    try {
      const res = await mikrotikApi.testServer(server.id);
      setTestResult(
        res.connected
          ? `'${server.name}': connected (${res.version})`
          : `'${server.name}': failed — ${res.error || "unknown error"}`
      );
    } catch (e) {
      setTestResult(e instanceof Error ? e.message : "Test failed");
    } finally {
      setTestingId(null);
    }
  };

  const handleDelete = async (server: MikroTikServer) => {
    if (!window.confirm(`Delete MikroTik server '${server.name}'?`)) return;
    try {
      await mikrotikApi.deleteServer(server.id);
      if (testResult) setTestResult(null);
      loadServers();
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Delete failed");
    }
  };

  return (
    <>
      <PageHeader title="MikroTik" subtitle="RouterOS access: SSH, Telnet, and WebFig proxy" />

      <div style={{ marginBottom: 12 }}>
        <button className="btn btn-primary" onClick={() => void openCreate()}>
          {showForm && editingId == null ? "Cancel" : "+ Add Server"}
        </button>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header">
            <div className="card-title">{editingId != null ? "Edit Server" : "New Server"}</div>
          </div>
          <div className="card-body">
            {formError && <div className="error-banner" style={{ marginBottom: 12 }}>{formError}</div>}
            <div className="form-grid">
              <div className="form-row">
                <label>Name *</label>
                <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="e.g. CORHQ hEX S" />
              </div>
              <div className="form-row">
                <label>Host / IP *</label>
                <input value={form.host} onChange={(e) => setForm((f) => ({ ...f, host: e.target.value }))} placeholder="e.g. 10.161.0.14" />
              </div>
              <div className="form-row">
                <label>SSH Port</label>
                <input type="number" value={form.ssh_port} onChange={(e) => setForm((f) => ({ ...f, ssh_port: parseInt(e.target.value) || 22 }))} />
              </div>
              <div className="form-row">
                <label>Username *</label>
                <input value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} placeholder="e.g. admin" />
              </div>
              <div className="form-row">
                <label>Password {editingId != null ? "(blank = keep)" : "*"}</label>
                <input type="password" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} />
              </div>
              <div className="form-row">
                <label>Relay Agent</label>
                <select
                  value={form.relay_agent_id ?? ""}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      relay_agent_id: e.target.value === "" ? null : Number(e.target.value),
                    }))
                  }
                >
                  <option value="">Direct connection (MissionControl server)</option>
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name} ({a.hostname}){a.status === "online" ? "" : ` — ${a.status}`}
                    </option>
                  ))}
                </select>
                <small className="form-hint">Use an on-site agent when the device is unreachable from this server.</small>
              </div>
              <div className="form-row">
                <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <input type="checkbox" checked={form.enabled} onChange={(e) => setForm((f) => ({ ...f, enabled: e.target.checked }))} />
                  <span>Enabled</span>
                </label>
              </div>
              <div className="form-row">
                <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <input type="checkbox" checked={form.telnet_enabled} onChange={(e) => setForm((f) => ({ ...f, telnet_enabled: e.target.checked }))} />
                  <span>Telnet fallback</span>
                </label>
                {form.telnet_enabled && (
                  <input type="number" value={form.telnet_port} style={{ marginTop: 6 }} onChange={(e) => setForm((f) => ({ ...f, telnet_port: parseInt(e.target.value) || 23 }))} />
                )}
              </div>
              <div className="form-row">
                <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <input type="checkbox" checked={form.api_enabled} onChange={(e) => setForm((f) => ({ ...f, api_enabled: e.target.checked }))} />
                  <span>REST API (WebFig port)</span>
                </label>
                {form.api_enabled && (
                  <input type="number" value={form.api_port} style={{ marginTop: 6 }} onChange={(e) => setForm((f) => ({ ...f, api_port: parseInt(e.target.value) || 443 }))} />
                )}
              </div>
            </div>
            <div style={{ display: "flex", gap: 10, marginTop: 14 }}>
              <button className="btn btn-primary" disabled={saving} onClick={() => void handleSave()}>
                {saving ? "Saving…" : editingId != null ? "Update" : "Create"}
              </button>
              <button className="btn btn-secondary" onClick={() => { setShowForm(false); setEditingId(null); }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {testResult && <div className="error-banner" style={{ marginBottom: 12 }}>{testResult}</div>}

      {loading ? (
        <div className="loading-bar">Loading MikroTik servers…</div>
      ) : servers.length === 0 ? (
        showForm ? null : (
          <div className="empty-state">
            No MikroTik servers configured yet.
            <div style={{ marginTop: 8 }}>Click “+ Add Server” above to register your first RouterOS device.</div>
          </div>
        )
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
                <span className="status-badge status-disabled">{server.status || "unknown"}</span>
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
                <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                  <a
                    className="btn btn-sm btn-secondary"
                    href={mikrotikApi.getWebfigUrl(server.id)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    WebFig
                  </a>
                  <button className="btn btn-sm btn-secondary" disabled={testingId === server.id} onClick={() => void handleTest(server)}>
                    {testingId === server.id ? "Testing…" : "Test"}
                  </button>
                  <button className="btn btn-sm btn-secondary" onClick={() => void openEdit(server)}>
                    Edit
                  </button>
                  <button className="btn btn-sm btn-danger" onClick={() => void handleDelete(server)}>
                    Delete
                  </button>
                </div>
                <div className="grid gap-1" style={{ marginTop: 12 }}>
                  <strong>Interfaces</strong>
                  {ifaceErrors[server.id] && (
                    <div className="muted">{ifaceErrors[server.id]}</div>
                  )}
                  {(interfaces[server.id] || []).length === 0 && (
                    <div className="empty-text">No cached interface data.</div>
                  )}
                  {(interfaces[server.id] || []).map((iface) => (
                    <div key={iface.name} style={{ display: "flex", gap: 12 }}>
                      <span>{iface.name}</span>
                      <span className="status-badge status-disabled">{iface.status || "unknown"}</span>
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
