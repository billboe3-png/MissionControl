import StatusBadge from "../common/StatusBadge";

interface HostAvailabilityCardProps {
    available: number;
    unavailable: number;
    total: number;
}

export default function HostAvailabilityCard({ available, unavailable, total }: HostAvailabilityCardProps) {
    return (
        <div className="ad-info-card">
            <h4>Host Availability</h4>
            <p><strong>Available:</strong> <StatusBadge status="healthy" label={String(available)} /></p>
            <p><strong>Unavailable:</strong> <StatusBadge status={unavailable > 0 ? "error" : "healthy"} label={String(unavailable)} /></p>
            <p><strong>Total:</strong> {total}</p>
        </div>
    );
}
