import { useEffect, useState } from "react";
import { useVeeamServer } from "../../contexts/VeeamServerContext";
import { ServerSelector } from "../../components/veeam/ServerSelector";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import {
    veeamApi,
    VeeamSession,
} from "../../services/veeam";

export default function VeeamSessionsPage() {
    const [sessions, setSessions] = useState<VeeamSession[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const { servers, selectedServerId } = useVeeamServer();

    useEffect(() => {
        // Servers fetched by VeeamServerProvider
    }, [selectedServerId]);

    useEffect(() => {
        if (loading) return;
        veeamApi.listSessions(selectedServerId).then((s) => {
            setSessions(s);
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }, [selectedServerId, loading]);

    const selectedServerName = servers.length > 0 ? servers.find(s => s.id === selectedServerId)?.name : "Veeam Server";

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;

    return (
        <>
            <PageHeader
                title="Veeam Sessions"
                subtitle={`${selectedServerName ?? "Veeam Server"} v1.0`}
            />
            {error && <div className="error-banner">{error}</div>}
            {loading && <div className="loading-bar" />}
            {!error && !loading && (
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Job ID</th>
                            <th>Session Type</th>
                            <th>State</th>
                            <th>Result</th>
                            <th>Duration</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sessions.map((session) => {
                            return (
                                <tr key={session.id}>
                                    <td>{session.name}</td>
                                    <td>{session.jobId}</td>
                                    <td>{session.sessionType}</td>
                                    <td>{session.state}</td>
                                    <td>{session.result?.result ?? "Unknown"}</td>
                                    <td>
                                        {session.creationTime && session.creationTime !== "Unknown" ? (
                                            <div>
                                                <div>Created: {session.creationTime}</div>
                                                {session.endTime && (
                                                    <div>Ended: {session.endTime}</div>
                                                )}
                                            </div>
                                        ) : null}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            )}
        {servers.length > 1 && <ServerSelector />}
        </>
    );
}
