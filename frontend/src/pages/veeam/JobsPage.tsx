import { useEffect, useState } from "react";
import { useVeeamServer } from "../../contexts/VeeamServerContext";
import { ServerSelector } from "../../components/veeam/ServerSelector";
import PageHeader from "../../components/common/PageHeader";
import { formatBytes } from "../../services/veeam";
import {
    veeamApi,
    VeeamJobDailyRow,
} from "../../services/veeam";

const DAY_PRESETS = [8, 14, 90] as const;
type DayPreset = (typeof DAY_PRESETS)[number];

function dateHeader(d: string): string {
    const [y, m, day] = d.split("-");
    const date = new Date(Date.UTC(Number(y), Number(m) - 1, Number(day)));
    const dow = date.toLocaleDateString("en-US", { weekday: "short" });
    return `${day}/${m} (${dow})`;
}

export default function VeeamJobsPage() {
    const [jobs, setJobs] = useState<VeeamJobDailyRow[]>([]);
    const [days, setDays] = useState<DayPreset>(8);
    const [dates, setDates] = useState<string[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const { servers, selectedServerId } = useVeeamServer();

    useEffect(() => {
        setLoading(true);
        setError(null);
        veeamApi
            .getJobStatsDaily(days, selectedServerId)
            .then((r) => {
                if (!r.success) {
                    setError(r.error ?? "Failed to load job stats");
                    return;
                }
                setJobs(r.jobs ?? []);
                setDates(r.dates ?? []);
            })
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, [days, selectedServerId]);

    const selectedServerName =
        servers.length > 0 ? servers.find((s) => s.id === selectedServerId)?.name : "Veeam Server";

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;

    return (
        <>
            <PageHeader
                title="Veeam Jobs"
                subtitle={`${selectedServerName ?? "Veeam Server"} v1.0`}
            />
            <div className="jobs-toolbar">
                <label className="jobs-days-label" htmlFor="veeam-job-days">
                    Days
                </label>
                <select
                    id="veeam-job-days"
                    className="jobs-days-select"
                    value={days}
                    onChange={(e) => setDays(Number(e.target.value) as DayPreset)}
                >
                    {DAY_PRESETS.map((d) => (
                        <option key={d} value={d}>
                            {d} days
                        </option>
                    ))}
                </select>
            </div>
            {jobs.length === 0 ? (
                <div className="data-table-empty">No job data available.</div>
            ) : (
                <div className="jobs-matrix-wrapper">
                    <table className="jobs-matrix">
                        <thead>
                            <tr>
                                <th className="jobs-matrix-name">VEEAM TASK</th>
                                <th>Run Time</th>
                                {dates.map((d) => (
                                    <th key={d}>{dateHeader(d)}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {jobs.map((job) => (
                                <tr key={job.job_name}>
                                    <td className="jobs-matrix-name">{job.job_name}</td>
                                    <td></td>
                                    {dates.map((d) => {
                                        const cell = (job.daily || {})[d];
                                        if (!cell) return <td key={d} className="cell-no-data" />;
                                        let cls = "cell-success";
                                        let content = formatBytes(
                                            cell.transferred_bytes ?? cell.processed_bytes ?? 0,
                                        );
                                        if (cell.failed_count > 0) {
                                            cls = "cell-failed";
                                            content = "X";
                                        } else if (cell.warning_count > 0) {
                                            cls = "cell-warning";
                                        }
                                        return (
                                            <td key={d} className={`jobs-matrix-cell ${cls}`}>
                                                {content}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
            {servers.length > 1 && <ServerSelector />}
        </>
    );
}
