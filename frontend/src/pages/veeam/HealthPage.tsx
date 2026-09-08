import { useEffect, useState } from "react";
import { useVeeamServer } from "../../contexts/VeeamServerContext";
import { ServerSelector } from "../../components/veeam/ServerSelector";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import {
    veeamApi,
    VeeamHealth,
} from "../../services/veeam";

export default function VeeamHealthPage() {
    const [health, setHealth] = useState<VeeamHealth | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const { servers, selectedServerId } = useVeeamServer();

    useEffect(() => {
        // Servers fetched by VeeamServerProvider
    }, [selectedServerId]);

    useEffect(() => {
        if (loading) return;
        veeamApi.getHealth(selectedServerId).then((h) => {
            setHealth(h);
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }, [selectedServerId, loading]);

    const selectedServerName = servers.length > 0 ? servers.find(s => s.id === selectedServerId)?.name : "Veeam Server";

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;
    if (!health) return null;

    return (
        <>
            <PageHeader
                title="Veeam Health"
                subtitle={`${selectedServerName ?? "Veeam Server"} v${health.version ?? "?"}`}
            />
            {health && (
                <div className="veeam-connection-status">
                    <StatusBadge
                        status={health.healthy ? "healthy" : "error"}
                        label={health.healthy ? "Connected" : "Error"}
                    />
                    <span>{health.healthy ? "Server reachable" : health.error}</span>
                </div>
            )}

        {servers.length > 1 && <ServerSelector />}
        </>
    );
}
