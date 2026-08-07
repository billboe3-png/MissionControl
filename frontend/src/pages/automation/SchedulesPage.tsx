import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import EmptyState from "../../components/common/EmptyState";
import StatusBadge from "../../components/common/StatusBadge";
import { useToast } from "../../contexts/ToastContext";
import { formatDateTime } from "../../utils/dateFormat";
import {
    automationApi,
    PlaybookScheduleData,
} from "../../services/automation";

export default function SchedulesPage() {
    const [items, setItems] = useState<PlaybookScheduleData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { showToast } = useToast();

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await automationApi.listSchedules();
            setItems(data.items);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to load schedules");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleDelete = async (id: number) => {
        if (!window.confirm("Delete this schedule?")) return;
        try {
            await automationApi.deleteSchedule(id);
            showToast("Schedule deleted", "success");
            loadData();
        } catch (e: unknown) {
            showToast(e instanceof Error ? e.message : "Delete failed", "error");
        }
    };

    return (
        <>
            <PageHeader
                title="Schedules"
                subtitle="Scheduled playbook executions"
            />
            {error && <div className="error-banner">{error}</div>}
            {loading ? (
                <div className="loading-bar" />
            ) : items.length === 0 ? (
                <EmptyState
                    icon="⏰"
                    title="No schedules"
                    description="Create schedules from playbook details."
                />
            ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                    {items.map((item) => (
                        <div
                            key={item.id}
                            className="card"
                            style={{ padding: "1rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}
                        >
                            <div>
                                <div style={{ fontWeight: 600 }}>{item.name}</div>
                                <div className="text-muted" style={{ fontSize: "0.85rem" }}>
                                    Playbook #{item.playbook_id} · {item.cron_expression}
                                </div>
                                <div className="text-muted" style={{ fontSize: "0.8rem" }}>
                                    {item.last_run ? `Last: ${formatDateTime(item.last_run)}` : "Never run"}
                                    {item.next_run ? ` · Next: ${formatDateTime(item.next_run)}` : ""}
                                </div>
                            </div>
                            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                                <StatusBadge
                                    status={item.enabled ? "healthy" : "neutral"}
                                    label={item.enabled ? "Active" : "Disabled"}
                                />
                                <button
                                    className="btn btn-danger btn-sm"
                                    onClick={() => handleDelete(item.id)}
                                >
                                    ×
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}
