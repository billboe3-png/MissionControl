import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import { api } from "../../services/api";
import { DashboardResponse } from "../../types/dashboard";

export default function SystemPage() {
    const [data, setData] = useState<DashboardResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        api
            .getDashboard()
            .then(setData)
            .catch((e) => setError(e.message));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (!data) return <div className="loading-bar" />;

    return (
        <>
            <PageHeader
                title="System"
                subtitle="Projects, tasks, and notes"
            />
            <div className="system-grid">
                <div className="system-card">
                    <h3>Projects</h3>
                    <p className="system-count">{data.projects.count}</p>
                    <ul className="system-list">
                        {data.projects.items.slice(0, 5).map((p) => (
                            <li key={p.id}>
                                <span>{p.name}</span>
                                <span className="system-status">{p.active ? "active" : "inactive"}</span>
                            </li>
                        ))}
                    </ul>
                </div>
                <div className="system-card">
                    <h3>Tasks</h3>
                    <p className="system-count">
                        {data.tasks.count} total
                        {data.tasks.statistics.blocked > 0 && (
                            <span className="system-overdue"> · {data.tasks.statistics.blocked} blocked</span>
                        )}
                    </p>
                </div>
                <div className="system-card">
                    <h3>Parking Lot</h3>
                    <p className="system-count">{data.parking_lot.count}</p>
                    <ul className="system-list">
                        {data.parking_lot.items.slice(0, 5).map((item) => (
                            <li key={item.id}>
                                <span>{item.title}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>
        </>
    );
}
