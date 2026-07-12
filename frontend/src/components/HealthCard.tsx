import { Health } from "../types/dashboard";

function healthBadgeClass(status: string): string {
    switch (status) {
        case "healthy":
            return "badge badge-success";
        case "warning":
            return "badge badge-warning";
        case "offline":
        case "unhealthy":
            return "badge badge-danger";
        default:
            return "badge badge-muted";
    }
}

interface HealthCardProps {
    health: Health;
}

export default function HealthCard({ health }: HealthCardProps) {
    return (
        <div className="card">
            <h2>Infrastructure Health</h2>

            <ul className="status-list">
                <li>
                    Backend
                    <span className={healthBadgeClass(health.backend.status)}>
                        {health.backend.status}
                    </span>
                </li>

                <li>
                    PostgreSQL
                    <span className={healthBadgeClass(health.database.status)}>
                        {health.database.status}
                    </span>
                </li>

                <li>
                    Redis
                    <span className={healthBadgeClass(health.redis.status)}>
                        {health.redis.status}
                    </span>
                </li>
            </ul>
        </div>
    );
}
