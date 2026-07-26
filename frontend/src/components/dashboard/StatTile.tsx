import { ReactNode } from "react";

interface StatTileProps {
    label: string;
    value: number | string;
    icon?: string;
    to?: string;
    variant?: "default" | "success" | "warning" | "danger" | "info";
    subtitle?: string;
    actions?: ReactNode;
}

const variantBorders: Record<string, string> = {
    default: "var(--text-muted)",
    success: "var(--success)",
    warning: "var(--warning)",
    danger: "var(--danger)",
    info: "var(--primary)",
};

export default function StatTile({
    label,
    value,
    icon,
    to,
    variant = "default",
    subtitle,
    actions,
}: StatTileProps) {
    const content = (
        <div
            className="stat-tile"
            style={{ borderLeftColor: variantBorders[variant] }}
        >
            <div className="stat-tile-body">
                {icon && <span className="stat-tile-icon">{icon}</span>}
                <div className="stat-tile-text">
                    <span className="stat-tile-value">{value}</span>
                    <span className="stat-tile-label">{label}</span>
                    {subtitle && (
                        <span className="stat-tile-subtitle">{subtitle}</span>
                    )}
                </div>
            </div>
            {actions && <div className="stat-tile-actions">{actions}</div>}
        </div>
    );

    if (to) {
        return (
            <a href={to} className="stat-tile-link">
                {content}
            </a>
        );
    }
    return content;
}
