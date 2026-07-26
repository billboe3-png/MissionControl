import WidgetCard from "./WidgetCard";
import { DashboardResponse } from "../../types/dashboard";

interface InfraWidgetProps {
    data: DashboardResponse | null;
}

export default function InfraWidget({ data }: InfraWidgetProps) {
    const companies = data?.integrations?.profiles?.count ?? 0;
    const sites = data?.projects?.count ?? 0;
    const plugins = data?.integrations?.profiles?.items?.length ?? 0;

    const items = [
        { label: "Companies", value: companies, icon: "🏢", to: "/companies" },
        { label: "Sites", value: sites, icon: "📍", to: "/infrastructure/system" },
        { label: "Registered Plugins", value: plugins, icon: "🧩", to: "/settings/integrations" },
        { label: "Active Integrations", value: data?.integrations?.profiles?.items?.filter(i => i.enabled).length ?? 0, icon: "🔗", to: "/settings/integrations" },
    ];

    return (
        <WidgetCard title="Infrastructure" icon="🏗️" to="/infrastructure">
            <div className="infra-widget-grid">
                {items.map((item) => (
                    <a key={item.label} href={item.to} className="infra-widget-tile">
                        <span className="infra-widget-icon">{item.icon}</span>
                        <span className="infra-widget-value">{item.value}</span>
                        <span className="infra-widget-label">{item.label}</span>
                    </a>
                ))}
            </div>
        </WidgetCard>
    );
}
