import StatusBadge from "../common/StatusBadge";

interface TriggerStatusCardProps {
    problemCount: number;
    okCount: number;
    enabledCount: number;
    disabledCount: number;
}

export default function TriggerStatusCard({ problemCount, okCount, enabledCount, disabledCount }: TriggerStatusCardProps) {
    return (
        <div className="ad-info-card">
            <h4>Trigger Status</h4>
            <p><strong>PROBLEM:</strong> <StatusBadge status={problemCount > 0 ? "error" : "healthy"} label={String(problemCount)} /></p>
            <p><strong>OK:</strong> <StatusBadge status="healthy" label={String(okCount)} /></p>
            <p><strong>Enabled:</strong> {enabledCount}</p>
            <p><strong>Disabled:</strong> {disabledCount}</p>
        </div>
    );
}
