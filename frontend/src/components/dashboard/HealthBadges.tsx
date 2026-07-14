import StatusBadge from "../common/StatusBadge";

interface HealthEntry {
    label: string;
    status: "healthy" | "warning" | "error" | "neutral";
}

export default function HealthBadges({ items }: { items: HealthEntry[] }) {
    return (
        <div className="health-badges">
            {items.map((item) => (
                <StatusBadge key={item.label} status={item.status} label={item.label} />
            ))}
        </div>
    );
}
