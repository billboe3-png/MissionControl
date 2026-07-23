import { useEffect, useState, useRef } from "react";
import * as XLSX from "xlsx";
import PageHeader from "../../components/common/PageHeader";
import {
    veeamApi,
    VeeamJobDailyRow,
    VeeamJobDailyCell,
    formatBytes,
} from "../../services/veeam";

const DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

const DATE_RANGE_OPTIONS = [
    { label: "7 days", value: 7 },
    { label: "14 days", value: 14 },
    { label: "30 days", value: 30 },
    { label: "60 days", value: 60 },
    { label: "90 days", value: 90 },
];

function formatShortDate(dateStr: string): string {
    const d = new Date(dateStr + "T00:00:00");
    return `${d.getDate().toString().padStart(2, "0")}/${(d.getMonth() + 1).toString().padStart(2, "0")}`;
}

function getDayOfWeek(dateStr: string): string {
    const d = new Date(dateStr + "T00:00:00");
    return DAY_NAMES[d.getDay()];
}

function formatBytesShort(bytes: number): string {
    if (bytes === 0) return "0 B";
    const abs = Math.abs(bytes);
    if (abs < 1024) return `${bytes} B`;
    if (abs < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (abs < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    if (abs < 1024 * 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
    return `${(bytes / (1024 * 1024 * 1024 * 1024)).toFixed(1)} TB`;
}

function cellClass(cell: VeeamJobDailyCell | undefined): string {
    if (!cell) return "";
    if (cell.failed_count > 0) return "cell-failed";
    if (cell.warning_count > 0) return "cell-warning";
    return "cell-success";
}

function exportToExcel(jobRows: VeeamJobDailyRow[], dates: string[], dateRange: number) {
    const uniqueServers = [...new Set(jobRows.map((r) => r.server_name ?? "").filter(Boolean))];
    const hasMultiServer = uniqueServers.length > 1;

    const ws: (string | number)[][] = [];

    const headerRow: (string | number)[] = [];
    if (hasMultiServer) headerRow.push("SERVER");
    headerRow.push("VEEAM TASK", "Run Time");
    for (const d of dates) {
        headerRow.push(`${formatShortDate(d)} (${getDayOfWeek(d)})`);
    }
    ws.push(headerRow);

    const totalsRow: (string | number)[] = [];
    if (hasMultiServer) totalsRow.push("");
    totalsRow.push("TOTAL", "");
    const dayTotals: number[] = dates.map(() => 0);

    for (const row of jobRows) {
        const dataRow: (string | number)[] = [];
        if (hasMultiServer) dataRow.push(row.server_name ?? "");
        dataRow.push(row.job_name, "");
        for (let i = 0; i < dates.length; i++) {
            const cell = row.daily[dates[i]];
            if (cell && cell.stored_bytes > 0) {
                dataRow.push(formatBytesShort(cell.stored_bytes));
                dayTotals[i] += cell.stored_bytes;
            } else {
                dataRow.push(cell ? "X" : "");
            }
        }
        ws.push(dataRow);
    }

    for (const total of dayTotals) {
        totalsRow.push(total > 0 ? formatBytesShort(total) : "");
    }
    ws.push(totalsRow);

    const wb = XLSX.utils.book_new();
    const sheet = XLSX.utils.aoa_to_sheet(ws);

    const colWidths = [{ wch: 40 }, { wch: 10 }];
    for (let i = 0; i < dates.length; i++) {
        colWidths.push({ wch: 14 });
    }
    sheet["!cols"] = colWidths;

    const lastCol = XLSX.utils.encode_col(dates.length + 2);
    const lastRow = jobRows.length + 2;
    sheet["!autofilter"] = { ref: `A1:${lastCol}${lastRow}` };

    XLSX.utils.book_append_sheet(wb, sheet, "Backup Jobs Report");

    const dateStr = new Date().toISOString().slice(0, 10);
    XLSX.writeFile(wb, `Veeam_Backup_Jobs_Report_${dateRange}d_${dateStr}.xlsx`);
}

export default function VeeamJobsPage() {
    const [jobRows, setJobRows] = useState<VeeamJobDailyRow[]>([]);
    const [dates, setDates] = useState<string[]>([]);
    const [serverNames, setServerNames] = useState<string[]>([]);
    const [sshAvailable, setSshAvailable] = useState(false);
    const [loading, setLoading] = useState(true);
    const [longLoad, setLongLoad] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [dateRange, setDateRange] = useState(7);
    const [selectedServer, setSelectedServer] = useState<string | null>(null);

    useEffect(() => {
        setLoading(true);
        setLongLoad(false);
        const timer = setTimeout(() => setLongLoad(true), 15000);
        veeamApi
            .getJobStatsDaily(dateRange)
            .then((resp) => {
                setJobRows(resp.jobs ?? []);
                setDates(resp.dates ?? []);
                setServerNames(resp.server_names ?? []);
                setSshAvailable(resp.ssh_available ?? false);
            })
            .catch((e) => setError(e.message))
            .finally(() => { clearTimeout(timer); setLongLoad(false); setLoading(false); });
    }, [dateRange]);

    const uniqueServers = serverNames.length > 0 ? serverNames : [...new Set(jobRows.map((r) => r.server_name ?? "").filter(Boolean))];
    const hasMultiServer = uniqueServers.length > 1;

    const filteredRows = selectedServer
        ? jobRows.filter((r) => r.server_name === selectedServer)
        : jobRows;

    if (loading) return (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "4rem 2rem" }}>
            <div className="loading-bar" style={{ width: "200px", marginBottom: longLoad ? "1.5rem" : 0 }} />
            {longLoad && (
                <div style={{ textAlign: "center", color: "#8b949e", fontSize: "0.85rem", lineHeight: 1.6 }}>
                    <div style={{ marginBottom: "0.5rem" }}>Connecting to Veeam servers for the first time...</div>
                    <div style={{ color: "#6e7681" }}>This takes about 2 minutes while we detect each server&apos;s database engine. Subsequent loads will be fast.</div>
                </div>
            )}
        </div>
    );
    if (error) return <div className="error-banner">{error}</div>;

    return (
        <>
            <PageHeader
                title="Backup Jobs"
                subtitle={`${jobRows.length} jobs across ${hasMultiServer ? uniqueServers.length + " servers" : "1 server"} over the last ${dateRange} days`}
            />
            {!sshAvailable && (
                <div className="info-banner" style={{ marginBottom: "1rem", padding: "0.75rem 1rem", background: "#1a3a5c", border: "1px solid #2a5a8c", borderRadius: "6px", color: "#b8d4f0" }}>
                    SSH bridge not configured. Configure SSH connection to the Veeam server to view job transfer statistics.
                </div>
            )}
            {hasMultiServer && (
                <div style={{ marginBottom: "0.75rem", display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
                    <span style={{ fontSize: "0.75rem", color: "#8b949e", marginRight: "0.25rem" }}>Servers:</span>
                    <button
                        onClick={() => setSelectedServer(null)}
                        style={{
                            fontSize: "0.75rem", padding: "0.3rem 0.7rem", borderRadius: "4px", cursor: "pointer", border: "1px solid",
                            borderColor: !selectedServer ? "#58a6ff" : "#30363d",
                            background: !selectedServer ? "#1a3a5c" : "#161b22",
                            color: !selectedServer ? "#b8d4f0" : "#8b949e",
                            fontWeight: !selectedServer ? 600 : 400,
                        }}
                    >
                        All ({jobRows.length})
                    </button>
                    {uniqueServers.map((srv) => {
                        const count = jobRows.filter((r) => r.server_name === srv).length;
                        const active = selectedServer === srv;
                        return (
                            <button
                                key={srv}
                                onClick={() => setSelectedServer(active ? null : srv)}
                                style={{
                                    fontSize: "0.75rem", padding: "0.3rem 0.7rem", borderRadius: "4px", cursor: "pointer", border: "1px solid",
                                    borderColor: active ? "#58a6ff" : "#30363d",
                                    background: active ? "#1a3a5c" : "#161b22",
                                    color: active ? "#b8d4f0" : "#8b949e",
                                    fontWeight: active ? 600 : 400,
                                }}
                            >
                                {srv} ({count})
                            </button>
                        );
                    })}
                </div>
            )}
            <div className="jobs-controls">
                <label style={{ fontSize: "0.85rem", color: "#8b949e" }}>
                    Date range:&nbsp;
                    <select
                        className="form-select"
                        value={dateRange}
                        onChange={(e) => setDateRange(Number(e.target.value))}
                        style={{ padding: "0.3rem 0.5rem", borderRadius: "4px", border: "1px solid #30363d", background: "#0d1117", color: "#c9d1d9" }}
                    >
                        {DATE_RANGE_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                                {opt.label}
                            </option>
                        ))}
                    </select>
                </label>
                <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                    <div style={{ display: "flex", gap: "1rem", fontSize: "0.75rem", color: "#8b949e" }}>
                        <span><span style={{ display: "inline-block", width: 10, height: 10, background: "#238636", borderRadius: 2, marginRight: 4, verticalAlign: "middle" }} /> Success</span>
                        <span><span style={{ display: "inline-block", width: 10, height: 10, background: "#9e6a03", borderRadius: 2, marginRight: 4, verticalAlign: "middle" }} /> Warning</span>
                        <span><span style={{ display: "inline-block", width: 10, height: 10, background: "#da3633", borderRadius: 2, marginRight: 4, verticalAlign: "middle" }} /> Failed</span>
                    </div>
                    <button
                        className="btn btn-secondary"
                        onClick={() => exportToExcel(filteredRows, dates, dateRange)}
                        disabled={filteredRows.length === 0}
                        style={{ fontSize: "0.8rem", padding: "0.3rem 0.75rem" }}
                    >
                        Export to Excel
                    </button>
                </div>
            </div>
            <div className="jobs-matrix-wrapper">
                <table className="jobs-matrix">
                    <thead>
                        <tr>
                            {hasMultiServer && <th className="jobs-matrix-server" style={{ fontSize: "0.7rem", color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.05em" }}>SERVER</th>}
                            <th className="jobs-matrix-name">VEEAM TASK</th>
                            {dates.map((d) => (
                                <th key={d} className="jobs-matrix-date">
                                    <div>{formatShortDate(d)}</div>
                                    <div className="jobs-matrix-dow">{getDayOfWeek(d)}</div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {filteredRows.map((row, idx) => (
                            <tr key={`${row.server_name ?? ""}-${row.job_name}-${idx}`}>
                                {hasMultiServer && (
                                    <td className="jobs-matrix-server" style={{ fontSize: "0.75rem", color: "#8b949e", maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                        {row.server_name ?? ""}
                                    </td>
                                )}
                                <td className="jobs-matrix-name">{row.job_name}</td>
                                {dates.map((d) => {
                                    const cell = row.daily[d];
                                    return (
                                        <td key={d} className={`jobs-matrix-cell ${cellClass(cell)}`}>
                                            {cell && cell.stored_bytes > 0
                                                ? <><span className="cell-icon">&#10003;</span> {formatBytesShort(cell.stored_bytes)}</>
                                                : cell
                                                    ? <span className="cell-icon cell-no-data">&#10007;</span>
                                                    : <span className="cell-icon cell-no-data">&#10007;</span>
                                            }
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                        {filteredRows.length > 0 && (
                            <tr className="jobs-matrix-total">
                                {hasMultiServer && <td />}
                                <td className="jobs-matrix-name">TOTAL</td>
                                {dates.map((d) => {
                                    const total = filteredRows.reduce((sum, row) => {
                                        const cell = row.daily[d];
                                        return sum + (cell ? cell.stored_bytes : 0);
                                    }, 0);
                                    return (
                                        <td key={d} className="jobs-matrix-cell jobs-matrix-total-cell">
                                            {total > 0 ? formatBytesShort(total) : ""}
                                        </td>
                                    );
                                })}
                            </tr>
                        )}
                        {filteredRows.length === 0 && (
                            <tr>
                                <td colSpan={(hasMultiServer ? 1 : 0) + dates.length + 1} className="empty-state">
                                    No job data found
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </>
    );
}
