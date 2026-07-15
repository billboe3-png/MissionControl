import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import EmptyState from "../../components/common/EmptyState";
import HyperVHostSelector, { useSelectedHost } from "../../components/hyperv/HyperVHostSelector";
import { hypervApi, HyperVNetwork } from "../../services/hyperv";

const typeColors: Record<string, "healthy" | "info" | "neutral"> = {
    external: "healthy",
    internal: "info",
    private: "neutral",
};

export default function NetworksPage() {
    const { selectedHostId, hosts, loading: hostsLoading } = useSelectedHost();
    const [networks, setNetworks] = useState<HyperVNetwork[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (hostsLoading) return;
        setLoading(true);
        hypervApi.listNetworks(selectedHostId)
            .then(setNetworks)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, [selectedHostId, hostsLoading]);

    if (hostsLoading) return <div className="loading">Loading…</div>;

    return (
        <>
            <PageHeader
                title="Virtual Networks"
                subtitle="Hyper-V virtual switches"
                actions={<HyperVHostSelector hosts={hosts} selectedHostId={selectedHostId} onChange={() => {}} />}
            />
            {loading ? (
                <div className="loading">Loading…</div>
            ) : (
                <>
                    {error && <div className="error-banner">{error}</div>}
                    {networks.length === 0 ? (
                        <EmptyState icon="🌐" title="No networks" description="No virtual switches found." />
                    ) : (
                        <div className="hyperv-network-grid">
                            {networks.map((net) => (
                                <div key={net.id} className="hyperv-network-card">
                                    <div className="hyperv-network-header">
                                        <h3>{net.name}</h3>
                                        <StatusBadge
                                            status={typeColors[net.switch_type] ?? "neutral"}
                                            label={net.switch_type}
                                        />
                                    </div>
                                    <div className="hyperv-network-meta">
                                        <span>Connected VMs: {net.connected_vms}</span>
                                        {net.vlan_id !== null && <span>VLAN: {net.vlan_id}</span>}
                                        <span>MAC Spoofing: {net.mac_address_spoofing ? "Enabled" : "Disabled"}</span>
                                        <span>Management OS: {net.allow_management_os ? "Yes" : "No"}</span>
                                        {net.net_adapter && <span>Adapter: {net.net_adapter}</span>}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}
        </>
    );
}
