import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { api } from "../../services/api";
import { DashboardResponse } from "../../types/dashboard";

export default function GitPage() {
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

    const { git } = data;

    return (
        <>
            <PageHeader
                title="Git"
                subtitle="Repository status"
            />
            <div className="git-stats">
                <div className="git-stat">
                    <span className="git-stat-label">Repository</span>
                    <span className="git-stat-value">{git.repository_name ?? "—"}</span>
                </div>
                <div className="git-stat">
                    <span className="git-stat-label">Branch</span>
                    <span className="git-stat-value">{git.current_branch ?? "—"}</span>
                </div>
                <div className="git-stat">
                    <span className="git-stat-label">Working Tree</span>
                    <StatusBadge
                        status={git.working_tree_clean ? "healthy" : "warning"}
                        label={git.working_tree_clean ? "clean" : "dirty"}
                    />
                </div>
            </div>
            {git.latest_commit && (
                <div className="docker-container-list">
                    <h3>Latest Commit</h3>
                    <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                        {git.latest_commit}
                        {git.commit_author && ` — ${git.commit_author}`}
                        {git.commit_date && ` on ${git.commit_date}`}
                    </p>
                </div>
            )}
        </>
    );
}
