import { ZabbixDashboard } from "../../services/zabbix";

interface DashboardCardProps {
    dashboard: ZabbixDashboard;
}

export default function DashboardCard({ dashboard }: DashboardCardProps) {
    return (
        <div className="ad-info-card">
            <h4>{dashboard.display_name || dashboard.name}</h4>
            <p><strong>Owner:</strong> {dashboard.owner}</p>
            <p><strong>Pages:</strong> {dashboard.pages}</p>
        </div>
    );
}
