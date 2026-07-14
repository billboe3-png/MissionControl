import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import ZabbixSummaryCard from "../../components/zabbix/ZabbixSummaryCard";
import ProblemSeverityCard from "../../components/zabbix/ProblemSeverityCard";
import LatestEventsCard from "../../components/zabbix/LatestEventsCard";
import { zabbixApi, ZabbixSummary, ZabbixProblemsResponse, ZabbixEventsResponse } from "../../services/zabbix";

export default function ZabbixOverviewPage() {
    const [summary, setSummary] = useState<ZabbixSummary | null>(null);
    const [problems, setProblems] = useState<ZabbixProblemsResponse | null>(null);
    const [events, setEvents] = useState<ZabbixEventsResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            zabbixApi.getOverview(),
            zabbixApi.getProblems(),
            zabbixApi.getEvents(),
        ])
            .then(([s, p, e]) => { setSummary(s); setProblems(p); setEvents(e); })
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading">Loading…</div>;

    return (
        <>
            <PageHeader title="Zabbix Monitoring" subtitle={summary?.version ? `Zabbix ${summary.version}` : "Monitoring overview"} />
            <div className="infra-overview-grid">
                <ZabbixSummaryCard label="Status" value={summary?.connected ? "Connected" : "Disconnected"} connected={summary?.connected ?? false} />
                <ZabbixSummaryCard label="Hosts" value={summary?.host_count ?? 0} connected={summary?.connected ?? false} />
                <ZabbixSummaryCard label="Problems" value={summary?.problem_count ?? 0} connected={summary?.connected ?? false} />
                <ZabbixSummaryCard label="Critical" value={summary?.critical_count ?? 0} connected={summary?.connected ?? false} />
                <ZabbixSummaryCard label="Warning" value={summary?.warning_count ?? 0} connected={summary?.connected ?? false} />
                <ZabbixSummaryCard label="API Latency" value={`${summary?.api_latency_ms ?? 0}ms`} connected={summary?.connected ?? false} />
            </div>
            <div className="identity-overview-section">
                <h3>Problems by Severity</h3>
                <div className="infra-overview-grid">
                    {Object.entries(problems?.severity_counts ?? {}).map(([sev, count]) => (
                        <ProblemSeverityCard key={sev} severity={sev} count={count} />
                    ))}
                    {(!problems || problems.total_count === 0) && <p>No active problems</p>}
                </div>
            </div>
            <div className="identity-overview-section">
                <h3>Recent Events</h3>
                <LatestEventsCard events={events?.events ?? []} max={10} />
            </div>
        </>
    );
}
