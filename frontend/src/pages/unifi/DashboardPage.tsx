import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { unifiPluginApi, UniFiSummary } from "../../services/unifiPlugin";

function fmtUptime(seconds: number): string {
    if (!seconds) return "—";
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    if (d > 0) return `${d}d ${h}h`;
    return `${h}h`;
}

export default function UniFiDashboardPage() {
    const navigate = useNavigate();
    const [summary, setSummary] = useState<UniFiSummary | null>(null);
    const [controllers, setControllers] = useState<{ healthy: number; total: number }>({
        healthy: 0,
        total: 0,
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        Promise.all([unifiPluginApi.getSummary(), unifiPluginApi.listControllers()])
            .then(([s, cs]) => {
                setSummary(s);
                setControllers({
                    healthy: cs.filter((c) => c.status === "healthy").length,
                    total: cs.length,
                });
            })
            .catch((e: Error) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading-bar" />;

    const s = summary!;
    const configured = s.controller_count > 0;
    const subtitle = configured
        ? `${s.controller_count} controller(s) · ${controllers.healthy} healthy`
        : "No UniFi controllers configured";

    const cards = [
        { label: "Status", value: configured ? "Connected" : "Not Configured", connected: configured, to: "/unifi/controllers" },
        { label: "Sites", value: s.site_count, connected: configured, to: "/unifi/sites" },
        { label: "Devices", value: s.device_count, connected: configured, to: "/unifi/devices" },
        { label: "Online Devices", value: s.online_devices, connected: configured, to: "/unifi/devices" },
        { label: "Clients", value: s.client_count, connected: configured, to: "/unifi/clients" },
        { label: "Alerts", value: s.alert_count, connected: configured, to: "/unifi/alerts" },
        { label: "Access Points", value: `${s.online_ap}/${s.ap_count}`, connected: configured, to: "/unifi/devices?type=access_point" },
        { label: "Switches", value: `${s.online_switch}/${s.switch_count}`, connected: configured, to: "/unifi/devices?type=switch" },
        { label: "Gateways", value: `${s.online_gateway}/${s.gateway_count}`, connected: configured, to: "/unifi/devices?type=gateway" },
    ];

    return (
        <>
            <PageHeader title="UniFi Network" subtitle={subtitle} />
            <div className="infra-overview-grid">
                {cards.map((c) => (
                    <div
                        key={c.label}
                        className="summary-card clickable"
                        onClick={() => navigate(c.to)}
                    >
                        <div className="summary-card-label">{c.label}</div>
                        <div className="summary-card-value">{c.value}</div>
                    </div>
                ))}
            </div>

            {!configured && (
                <div className="identity-overview-section">
                    <div className="error-banner">
                        No UniFi controllers are configured. Add a controller in the
                        Integrations settings (UniFi Site Manager API key) or the
                        plugin config, then trigger a sync.
                    </div>
                </div>
            )}

            <div className="identity-overview-section">
                <h3>Devices by Status</h3>
                <div className="infra-overview-grid">
                    <div className="summary-card">
                        <div className="summary-card-label">Online</div>
                        <div className="summary-card-value">{s.online_devices}</div>
                    </div>
                    <div className="summary-card">
                        <div className="summary-card-label">Offline</div>
                        <div className="summary-card-value">{s.offline_devices}</div>
                    </div>
                    <div className="summary-card">
                        <div className="summary-card-label">Wireless Networks</div>
                        <div className="summary-card-value">{s.wireless_network_count}</div>
                    </div>
                    <div className="summary-card">
                        <div className="summary-card-label">Unacked Alerts</div>
                        <div className="summary-card-value">{s.unacknowledged_alerts}</div>
                    </div>
                </div>
            </div>
        </>
    );
}

export { fmtUptime };
