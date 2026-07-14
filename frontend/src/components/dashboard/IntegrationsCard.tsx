import { useNavigate } from "react-router-dom";

interface IntegrationItem {
    id: number;
    name: string;
    type: string;
    enabled: boolean;
    connected: boolean;
    last_test: string | null;
}

interface IntegrationsCardProps {
    items: IntegrationItem[];
}

const TYPE_ICONS: Record<string, string> = {
    zabbix: "📡",
    active_directory: "🏢",
    microsoft_365: "☁️",
};

export default function IntegrationsCard({ items }: IntegrationsCardProps) {
    const navigate = useNavigate();

    return (
        <div className="dashboard-section integrations-card">
            <div className="integrations-card-header">
                <h3>Integrations</h3>
                <button
                    className="btn btn-link btn-sm"
                    onClick={() => navigate("/settings/integrations")}
                >
                    Manage
                </button>
            </div>
            {items.length === 0 ? (
                <p className="settings-hint">No integrations configured.</p>
            ) : (
                <div className="integrations-list">
                    {items.map((item) => (
                        <div key={item.id} className="integrations-list-item">
                            <span className="integrations-item-icon">
                                {TYPE_ICONS[item.type] ?? "🔌"}
                            </span>
                            <span className="integrations-item-name">{item.name}</span>
                            <span
                                className={`integrations-item-status ${
                                    item.connected
                                        ? "healthy"
                                        : item.enabled
                                            ? "warning"
                                            : "neutral"
                                }`}
                            >
                                {item.connected
                                    ? "Connected"
                                    : item.enabled
                                        ? "Enabled"
                                        : "Disabled"}
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
