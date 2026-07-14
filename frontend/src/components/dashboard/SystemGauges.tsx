interface GaugeProps {
    label: string;
    value: number;
    max?: number;
    unit?: string;
}

function GaugeBar({ label, value, max = 100, unit = "" }: GaugeProps) {
    const pct = Math.min(100, Math.round((value / max) * 100));
    const color = pct >= 90 ? "red" : pct >= 70 ? "amber" : "green";

    return (
        <div className="gauge-item">
            <div className="gauge-header">
                <span className="gauge-label">{label}</span>
                <span className="gauge-value">
                    {value}{unit}
                </span>
            </div>
            <div className="gauge-bar">
                <div
                    className={`gauge-fill gauge-${color}`}
                    style={{ width: `${pct}%` }}
                />
            </div>
        </div>
    );
}

export default function SystemGauges({
    cpu,
    memory,
    disk,
}: {
    cpu?: number;
    memory?: number;
    disk?: number;
}) {
    return (
        <div className="system-gauges">
            {cpu !== undefined && <GaugeBar label="CPU" value={cpu} unit="%" />}
            {memory !== undefined && <GaugeBar label="Memory" value={memory} unit="%" />}
            {disk !== undefined && <GaugeBar label="Disk" value={disk} unit="%" />}
        </div>
    );
}
