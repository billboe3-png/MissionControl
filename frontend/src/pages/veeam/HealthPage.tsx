import { useCallback, useEffect, useState } from "react";
import { useVeeamServer } from "../../contexts/VeeamServerContext";
import VeeamPageShell from "../../components/veeam/VeeamPageShell";
import StatusBadge from "../../components/common/StatusBadge";
import {
    veeamApi,
    VeeamHealth,
} from "../../services/veeam";

export default function VeeamHealthPage() {
    const [health, setHealth] = useState<VeeamHealth | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const { selectedServerId } = useVeeamServer();

    const load = useCallback(() => {
        setLoading(true);
        setError(null);
        veeamApi
            .getHealth(selectedServerId)
            .then(setHealth)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, [selectedServerId]);

    useEffect(() => {
        load();
    }, [load]);

    return (
        <VeeamPageShell
            title="Veeam Health"
            version={health?.version ?? "?"}
            onRefresh={load}
            refreshing={loading}
        >
            {error && <div className="error-banner">{error}</div>}
            {loading && <div className="loading-bar" />}
            {health && (
                <div className="veeam-connection-status">
                    <StatusBadge
                        status={health.healthy ? "healthy" : "error"}
                        label={health.healthy ? "Connected" : "Error"}
                    />
                    <span>{health.healthy ? "Server reachable" : health.error}</span>
                </div>
            )}
        </VeeamPageShell>
    );
}
