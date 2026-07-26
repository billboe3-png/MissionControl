import { Link } from "react-router-dom";

const actions = [
    { label: "Add Host", path: "/remote/hosts", icon: "🖥️" },
    { label: "Execute Command", path: "/remote/execute", icon: "⚡" },
    { label: "System Health", path: "/infrastructure/health", icon: "❤️" },
];

export default function QuickActions() {
    return (
        <div className="quick-actions">
            {actions.map((action) => (
                <Link key={action.path} to={action.path} className="quick-action-btn">
                    <span className="quick-action-icon">{action.icon}</span>
                    <span className="quick-action-label">{action.label}</span>
                </Link>
            ))}
        </div>
    );
}
