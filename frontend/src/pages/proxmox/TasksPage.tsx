import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import EmptyState from "../../components/common/EmptyState";
import { proxmoxApi, ProxmoxTask } from "../../services/proxmox";

const statusColors: Record<string, "healthy" | "warning" | "error" | "neutral"> = {
    ok: "healthy",
    running: "warning",
    failed: "error",
    unknown: "neutral",
};

export default function TasksPage() {
    const [tasks, setTasks] = useState<ProxmoxTask[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        proxmoxApi.listTasks()
            .then(setTasks)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading-bar" />;

    return (
        <>
            <PageHeader title="Tasks" subtitle="Recent cluster tasks" />
            {error && <div className="error-banner">{error}</div>}
            {tasks.length === 0 ? (
                <EmptyState icon="📋" title="No tasks" description="No recent tasks found." />
            ) : (
                <div className="proxmox-tasks-table">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Node</th>
                                <th>Type</th>
                                <th>User</th>
                                <th>Status</th>
                                <th>Started</th>
                                <th>Ended</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tasks.map((task) => (
                                <tr key={task.id}>
                                    <td>{task.node}</td>
                                    <td>{task.type}</td>
                                    <td>{task.user}</td>
                                    <td>
                                        <StatusBadge
                                            status={statusColors[task.status] ?? "neutral"}
                                            label={task.status}
                                        />
                                    </td>
                                    <td>{task.start_time ? new Date(task.start_time).toLocaleString() : "—"}</td>
                                    <td>{task.end_time ? new Date(task.end_time).toLocaleString() : "—"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </>
    );
}
