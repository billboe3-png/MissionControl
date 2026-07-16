import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import HyperVHostSelector, { useSelectedHost } from "../../components/hyperv/HyperVHostSelector";
import { hypervApi, HyperVReplication, HyperVReplicationItem } from "../../services/hyperv";

function formatBytes(bytes: number): string {
    if (bytes === 0) return "0 B";
    const units = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

function healthStatus(h: string): "healthy" | "warning" | "error" {
    switch (h.toLowerCase()) {
        case "ok": return "healthy";
        case "warn": return "warning";
        case "critical": return "error";
        default: return "warning";
    }
}

function stateLabel(s: string): string {
    switch (s.toLowerCase()) {
        case "replicating": return "Replicating";
        case "waitforstatestore": return "Waiting";
        case "failedover": return "Failed Over";
        case "resynchronizing": return "Resyncing";
        case "disconnected": return "Disconnected";
        default: return s;
    }
}

function formatFrequency(sec: number): string {
    if (sec <= 0) return "—";
    if (sec < 60) return `${sec}s`;
    if (sec < 3600) return `${sec / 60}min`;
    return `${sec / 3600}hr`;
}

export default function HyperVReplicationPage() {
    const { selectedHostId, hosts, loading: hostsLoading, setSelectedHostId } = useSelectedHost();
    const [repl, setRepl] = useState<HyperVReplication | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (hostsLoading) return;
        setLoading(true);
        hypervApi.getReplication(selectedHostId)
            .then(setRepl)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, [selectedHostId, hostsLoading]);

    if (hostsLoading || loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;
    if (!repl) return null;

    return (
        <>
            <PageHeader
                title="Hyper-V Replication"
                subtitle="VM replication status and health"
                actions={<HyperVHostSelector hosts={hosts} selectedHostId={selectedHostId} onChange={setSelectedHostId} />}
            />

            <div className="ad-info-grid" style={{ marginBottom: 20 }}>
                <div className="ad-info-card">
                    <h4>Replication Overview</h4>
                    <p><strong>Total VMs with replication:</strong> {repl.total}</p>
                    <p><strong>Currently replicating:</strong> {repl.replicating}</p>
                </div>
                <div className="ad-info-card">
                    <h4>Status</h4>
                    <p>
                        <strong>Health:</strong>{" "}
                        <StatusBadge
                            status={repl.items.some((r) => r.health.toLowerCase() === "critical") ? "error"
                                : repl.items.some((r) => r.health.toLowerCase() === "warn") ? "warning"
                                : "healthy"}
                            label={repl.items.length === 0 ? "No replication configured"
                                : repl.items.every((r) => r.health.toLowerCase() === "ok") ? "All healthy"
                                : "Issues detected"}
                        />
                    </p>
                </div>
            </div>

            {repl.items.length === 0 ? (
                <div className="settings-hint">
                    No VM replication is configured on this host. Set up Hyper-V Replica to replicate VMs to a secondary server.
                </div>
            ) : (
                <div>
                    {repl.items.map((item, idx) => (
                        <ReplicationCard key={`${item.vm_name}-${idx}`} item={item} />
                    ))}
                </div>
            )}
        </>
    );
}

function ReplicationCard({ item }: { item: HyperVReplicationItem }) {
    return (
        <div className="hyperv-repl-card">
            <div className="hyperv-repl-card-header">
                <div>
                    <h4>{item.vm_name}</h4>
                    <span className="hyperv-repl-vm">
                        → {item.replica_server}:{item.replica_port}
                    </span>
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <StatusBadge
                        status={item.state.toLowerCase() === "replicating" ? "healthy" : "warning"}
                        label={stateLabel(item.state)}
                    />
                    <StatusBadge
                        status={healthStatus(item.health)}
                        label={`Health: ${item.health}`}
                    />
                </div>
            </div>
            <div className="hyperv-repl-details">
                <div className="hyperv-repl-detail">
                    <label>Frequency</label>
                    <span>{formatFrequency(item.frequency_seconds)}</span>
                </div>
                <div className="hyperv-repl-detail">
                    <label>Last Replication</label>
                    <span>{item.last_replication_time || "—"}</span>
                </div>
                <div className="hyperv-repl-detail">
                    <label>Bytes Sent</label>
                    <span>{formatBytes(item.bytes_sent)}</span>
                </div>
                <div className="hyperv-repl-detail">
                    <label>Bytes Received</label>
                    <span>{formatBytes(item.bytes_received)}</span>
                </div>
                <div className="hyperv-repl-detail">
                    <label>Result Code</label>
                    <span>{item.last_result_code === 0 ? "Success" : `Error ${item.last_result_code}`}</span>
                </div>
            </div>
        </div>
    );
}
