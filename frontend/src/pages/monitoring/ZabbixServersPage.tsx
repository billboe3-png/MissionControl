import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { zabbixPluginApi, ZabbixPluginServer } from "../../services/zabbixPlugin";
import { formatDateTime } from "../../utils/dateFormat";

export default function ZabbixServersPage() {
    const [servers, setServers] = useState<ZabbixPluginServer[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        zabbixPluginApi
            .listServers()
            .then(setServers)
            .catch((e: Error) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading-bar" />;

    return (
        <>
            <PageHeader
                title="Zabbix Servers"
                subtitle={`Plugin-managed servers (${servers.length})`}
                actions={
                    <button className="btn btn-primary" disabled>
                        Add Server
                    </button>
                }
            />
            {servers.length === 0 ? (
                <div className="identity-overview-section">
                    <p>No Zabbix servers configured via plugin.</p>
                    <p className="page-subtitle">
                        Servers are configured in <code>plugins/installed/zabbix/config.json</code> or
                        via the Integrations settings page.
                    </p>
                </div>
            ) : (
                <div className="identity-overview-section">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>URL</th>
                                <th>Status</th>
                                <th>Version</th>
                                <th>Last Sync</th>
                                <th>Error</th>
                            </tr>
                        </thead>
                        <tbody>
                            {servers.map((s) => (
                                <tr key={s.id}>
                                    <td>
                                        <strong>{s.name}</strong>
                                    </td>
                                    <td>
                                        <code>{s.url}</code>
                                    </td>
                                    <td>
                                        <StatusBadge
                                            status={
                                                s.status === "healthy"
                                                    ? "healthy"
                                                    : s.status === "error"
                                                      ? "error"
                                                      : "neutral"
                                            }
                                            label={s.status}
                                        />
                                    </td>
                                    <td>{s.version ?? "—"}</td>
                                    <td>
                                        {s.last_sync_at
                                            ? formatDateTime(s.last_sync_at)
                                            : "Never"}
                                    </td>
                                    <td>
                                        {s.last_error ? (
                                            <span className="text-danger" title={s.last_error}>
                                                {s.last_error.slice(0, 60)}
                                                {s.last_error.length > 60 ? "…" : ""}
                                            </span>
                                        ) : (
                                            "—"
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </>
    );
}
