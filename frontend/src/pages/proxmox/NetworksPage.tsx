import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import EmptyState from "../../components/common/EmptyState";
import { proxmoxApi, ProxmoxNetwork } from "../../services/proxmox";

const statusColors: Record<string, "healthy" | "warning" | "error" | "neutral"> = {
    active: "healthy",
    inactive: "error",
    unknown: "neutral",
};

export default function NetworksPage() {
    const [networks, setNetworks] = useState<ProxmoxNetwork[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        proxmoxApi.listNetworks()
            .then(setNetworks)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading">Loading…</div>;

    return (
        <>
            <PageHeader title="Networks" subtitle="Proxmox network interfaces" />
            {error && <div className="error-banner">{error}</div>}
            {networks.length === 0 ? (
                <EmptyState icon="🌐" title="No networks" description="No network interfaces found." />
            ) : (
                <div className="proxmox-networks-table">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Type</th>
                                <th>Node</th>
                                <th>CIDR</th>
                                <th>Status</th>
                                <th>VLAN</th>
                            </tr>
                        </thead>
                        <tbody>
                            {networks.map((net) => (
                                <tr key={net.id}>
                                    <td>{net.name}</td>
                                    <td>{net.type}</td>
                                    <td>{net.node}</td>
                                    <td>{net.cidr || "—"}</td>
                                    <td>
                                        <StatusBadge
                                            status={statusColors[net.status] ?? "neutral"}
                                            label={net.status}
                                        />
                                    </td>
                                    <td>{net.vlan_id !== null ? net.vlan_id : "—"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </>
    );
}
