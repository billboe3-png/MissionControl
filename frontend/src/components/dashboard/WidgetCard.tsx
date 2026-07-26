import { ReactNode } from "react";

interface WidgetCardProps {
    title: string;
    icon?: string;
    to?: string;
    actions?: ReactNode;
    children: ReactNode;
}

export default function WidgetCard({ title, icon, to, actions, children }: WidgetCardProps) {
    return (
        <div className="widget-card">
            <div className="widget-header">
                <div className="widget-title-group">
                    {icon && <span className="widget-icon">{icon}</span>}
                    <h3 className="widget-title">{title}</h3>
                </div>
                <div className="widget-actions">
                    {actions}
                    {to && (
                        <a href={to} className="widget-link">
                            View all
                        </a>
                    )}
                </div>
            </div>
            <div className="widget-body">{children}</div>
        </div>
    );
}
