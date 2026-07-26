import { useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import SearchInput from "../../components/common/SearchInput";

interface Plugin {
    id: string;
    name: string;
    version: string;
    sdk_version: string;
    enabled: boolean;
    health: string;
    type: string;
    description: string;
    dependencies: string[];
    update_available: boolean;
}

const MOCK_PLUGINS: Plugin[] = [];

export default function PluginCenterPage() {
    const [search, setSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState("all");
    const [_plugins] = useState<Plugin[]>(MOCK_PLUGINS);

    const plugins = _plugins.filter((p) => {
        if (statusFilter === "enabled" && !p.enabled) return false;
        if (statusFilter === "disabled" && p.enabled) return false;
        if (search) {
            const q = search.toLowerCase();
            return (
                p.name.toLowerCase().includes(q) ||
                p.description.toLowerCase().includes(q)
            );
        }
        return true;
    });

    const enabledCount = _plugins.filter((p) => p.enabled).length;
    const disabledCount = _plugins.filter((p) => !p.enabled).length;
    const updateCount = _plugins.filter((p) => p.update_available).length;

    return (
        <>
            <PageHeader
                title="Plugin Center"
                subtitle="Manage installed plugins and integrations"
            />

            <div className="fleet-stats-bar">
                <div className="fleet-stat-chip">
                    <span className="fleet-stat-chip-value">{_plugins.length}</span>
                    <span className="fleet-stat-chip-label">Total</span>
                </div>
                <div className="fleet-stat-chip success">
                    <span className="fleet-stat-chip-value">{enabledCount}</span>
                    <span className="fleet-stat-chip-label">Enabled</span>
                </div>
                <div className="fleet-stat-chip">
                    <span className="fleet-stat-chip-value">{disabledCount}</span>
                    <span className="fleet-stat-chip-label">Disabled</span>
                </div>
                {updateCount > 0 && (
                    <div className="fleet-stat-chip" style={{ borderLeftColor: "var(--warning)" }}>
                        <span className="fleet-stat-chip-value">{updateCount}</span>
                        <span className="fleet-stat-chip-label">Updates Available</span>
                    </div>
                )}
            </div>

            <div className="fleet-toolbar">
                <SearchInput value={search} onChange={setSearch} placeholder="Search plugins..." />
                <select
                    className="form-input fleet-filter"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                >
                    <option value="all">All</option>
                    <option value="enabled">Enabled</option>
                    <option value="disabled">Disabled</option>
                </select>
            </div>

            {plugins.length === 0 ? (
                <div className="empty-state">
                    <span className="empty-state-icon">🧩</span>
                    <h3 className="empty-state-title">No plugins installed</h3>
                    <p className="empty-state-description">
                        Plugins extend Mission Control with additional capabilities.
                        Community plugins will be available in a future release.
                    </p>
                </div>
            ) : (
                <div className="plugin-center-grid">
                    {plugins.map((plugin) => (
                        <div key={plugin.id} className="plugin-center-card">
                            <div className="plugin-center-header">
                                <div>
                                    <div className="plugin-center-name">{plugin.name}</div>
                                    <div className="plugin-center-meta">
                                        <span>v{plugin.version}</span>
                                        <span>SDK {plugin.sdk_version}</span>
                                        <span>{plugin.type}</span>
                                    </div>
                                </div>
                                <StatusBadge
                                    status={
                                        plugin.health === "healthy"
                                            ? "healthy"
                                            : plugin.health === "warning"
                                              ? "warning"
                                              : "error"
                                    }
                                    label={plugin.enabled ? "Enabled" : "Disabled"}
                                />
                            </div>
                            {plugin.description && (
                                <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                                    {plugin.description}
                                </div>
                            )}
                            {plugin.dependencies.length > 0 && (
                                <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                                    Dependencies: {plugin.dependencies.join(", ")}
                                </div>
                            )}
                            <div className="plugin-center-actions">
                                <button className="btn btn-sm btn-secondary">
                                    {plugin.enabled ? "Disable" : "Enable"}
                                </button>
                                <button className="btn btn-sm btn-secondary">Restart</button>
                                <button className="btn btn-sm btn-secondary">Configure</button>
                                <button className="btn btn-sm btn-secondary">Logs</button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}
