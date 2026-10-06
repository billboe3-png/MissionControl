import { useCallback, useEffect, useState } from "react";
import { useVeeamServer } from "../../contexts/VeeamServerContext";
import VeeamPageShell from "../../components/veeam/VeeamPageShell";
import {
    veeamApi,
    VeeamSession,
} from "../../services/veeam";

export default function VeeamSessionsPage() {
    const [sessions, setSessions] = useState<VeeamSession[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const { selectedServerId } = useVeeamServer();

    const load = useCallback(() => {
        setLoading(true);
        setError(null);
        veeamApi
            .listSessions(selectedServerId)
            .then(setSessions)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, [selectedServerId]);

    useEffect(() => {
        load();
    }, [load]);

    return (
        <VeeamPageShell title="Veeam Sessions" onRefresh={load} refreshing={loading}>
            {error && <div className="error-banner">{error}</div>}
            {loading && <div className="loading-bar" />}
            {!error && sessions.length === 0 && !loading && (
                <div className="data-table-empty">No sessions found.</div>
            )}
            {!error && sessions.length > 0 && (
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
        </VeeamPageShell>
    );
}
