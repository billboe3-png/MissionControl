import { useEffect, useState } from "react";
import { useVeeamServer } from "../../contexts/VeeamServerContext";
import { ServerSelector } from "../../components/veeam/ServerSelector";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge, { StatusType } from "../../components/common/StatusBadge";
import {
    veeamApi,
    VeeamJob,
    VeeamJobAction,
} from "../../services/veeam";

export default function VeeamJobsPage() {
    const [jobs, setJobs] = useState<VeeamJob[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const { servers, selectedServerId } = useVeeamServer();

    useEffect(() => {
        // Servers fetched by VeeamServerProvider
    }, [selectedServerId]);

    useEffect(() => {
        if (loading) return;
        veeamApi.listJobs(selectedServerId).then((j) => {
            setJobs(j.jobs);
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
                title="Veeam Jobs"
                subtitle={`${selectedServerName ?? "Veeam Server"} v1.0`}
            />
            {error && <div className="error-banner">{error}</div>}
            {loading && <div className="loading-bar" />}
            {!error && !loading && (
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Type</th>
                            <th>State</th>
                            <th>Schedule</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {jobs.map((job) => {
                            const st: { status: StatusType; label: string } =
                                job.state === "Stopped"
                                    ? { status: "healthy", label: "Idle" }
                                    : job.state === "Running"
                                        ? { status: "info", label: "Running" }
                                        : { status: "error", label: "Failed" };
                            return (
                                <tr key={job.id}>
                                    <td>{job.name}</td>
                                    <td>{job.type}</td>
                                    <td>
                                        <StatusBadge
                                            status={st.status}
                                            label={st.label}
                                        />
                                    </td>
                                    <td>{job.schedule?.kind ?? "Manual"}</td>
                                    <td>
                                        {job.state !== "Running" && (
                                            <button
                                                className="btn btn-sm btn-success"
                                                onClick={() =>
                                                    veeamApi.startJob(job.id, selectedServerId).catch(() => {})
                                                }
                                            >
                                                Start
                                            </button>
                                        )}
                                        {job.state === "Running" && (
                                            <button
                                                className="btn btn-sm btn-danger"
                                                onClick={() =>
                                                    veeamApi.stopJob(job.id, selectedServerId).catch(() => {})
                                                }
                                            >
                                                Stop
                                            </button>
                                        )}
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
