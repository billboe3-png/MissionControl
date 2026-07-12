import { SystemInfo } from "../types/dashboard";

function formatBytes(bytes: number): string {
    if (bytes === 0) return "0 B";
    const units = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

function formatUptime(seconds: number): string {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
}

interface SystemCardProps {
    system: SystemInfo;
}

export default function SystemCard({ system }: SystemCardProps) {
    return (
        <div className="card">
            <h2>System</h2>

            <ul className="status-list">
                <li>
                    Hostname
                    <span>{system.hostname}</span>
                </li>

                <li>
                    OS
                    <span>{system.os}</span>
                </li>

                <li>
                    CPU ({system.cpu_count} cores)
                    <span>{system.cpu_percent}%</span>
                </li>

                <li>
                    <div className="metric-bar-row">
                        <span>CPU Usage</span>
                        <span>{system.cpu_percent}%</span>
                    </div>
                    <div className="metric-bar">
                        <div
                            className={`metric-bar-fill ${system.cpu_percent > 80 ? "bar-danger" : system.cpu_percent > 60 ? "bar-warning" : "bar-success"}`}
                            style={{ width: `${Math.min(system.cpu_percent, 100)}%` }}
                        />
                    </div>
                </li>

                <li>
                    <div className="metric-bar-row">
                        <span>
                            Memory {formatBytes(system.memory_used)} /{" "}
                            {formatBytes(system.memory_total)}
                        </span>
                        <span>{system.memory_percent}%</span>
                    </div>
                    <div className="metric-bar">
                        <div
                            className={`metric-bar-fill ${system.memory_percent > 80 ? "bar-danger" : system.memory_percent > 60 ? "bar-warning" : "bar-success"}`}
                            style={{ width: `${Math.min(system.memory_percent, 100)}%` }}
                        />
                    </div>
                </li>

                <li>
                    <div className="metric-bar-row">
                        <span>
                            Disk {formatBytes(system.disk_used)} /{" "}
                            {formatBytes(system.disk_total)}
                        </span>
                        <span>{system.disk_percent}%</span>
                    </div>
                    <div className="metric-bar">
                        <div
                            className={`metric-bar-fill ${system.disk_percent > 80 ? "bar-danger" : system.disk_percent > 60 ? "bar-warning" : "bar-success"}`}
                            style={{ width: `${Math.min(system.disk_percent, 100)}%` }}
                        />
                    </div>
                </li>

                <li>
                    Uptime
                    <span>{formatUptime(system.uptime_seconds)}</span>
                </li>
            </ul>
        </div>
    );
}
