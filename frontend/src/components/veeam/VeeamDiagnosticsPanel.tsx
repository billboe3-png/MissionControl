import type { ReactNode } from "react";
import type { VeeamServerDiagnostics } from "../../services/veeam";

interface Props {
    result: VeeamServerDiagnostics;
    onClose: () => void;
}

function Row({ label, value }: { label: string; value: ReactNode }) {
    return (
        <div
            style={{
                display: "flex",
                justifyContent: "space-between",
                gap: "1rem",
                padding: "0.25rem 0",
                borderBottom: "1px solid #21262d",
            }}
        >
            <span style={{ color: "#8b949e" }}>{label}</span>
            <span style={{ color: "#c9d1d9", textAlign: "right" }}>{value}</span>
        </div>
    );
}

function SectionTitle({ children }: { children: ReactNode }) {
    return (
        <div style={{ fontWeight: 600, color: "#8b949e", margin: "0.75rem 0 0.25rem" }}>
            {children}
        </div>
    );
}

export default function VeeamDiagnosticsPanel({ result, onClose }: Props) {
    const { agent, db_detect, db_query, recommendations } = result;
    const healthy = result.success;
    const statusColor = healthy ? "green" : "red";

    return (
        <div
            style={{
                border: "1px solid #30363d",
                borderRadius: "8px",
                background: "#0d1117",
                padding: "1rem",
                marginBottom: "1rem",
            }}
        >
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "0.5rem",
                }}
            >
                <strong style={{ color: "#c9d1d9" }}>Diagnostics</strong>
                <span>
                    <span className={`status-badge ${statusColor}`}>
                        <span className="status-badge-dot" />
                        {healthy ? "Healthy" : "Issues found"}
                    </span>
                    <button
                        onClick={onClose}
                        style={{
                            marginLeft: "0.5rem",
                            background: "none",
                            border: "1px solid #30363d",
                            color: "#8b949e",
                            borderRadius: "4px",
                            cursor: "pointer",
                            padding: "0.1rem 0.5rem",
                            fontSize: "0.8rem",
                        }}
                    >
                        Close
                    </button>
                </span>
            </div>

            <div style={{ fontSize: "0.85rem", maxWidth: "38rem" }}>
                <SectionTitle>Agent relay</SectionTitle>
                <Row label="Status" value={agent.success ? "Connected" : "Failed"} />
                {agent.error && <Row label="Error" value={agent.error} />}
                {agent.db_available !== undefined && (
                    <Row
                        label="DB bridge"
                        value={agent.db_available ? "Available" : "Unavailable"}
                    />
                )}
                {agent.rest_available !== undefined && (
                    <Row
                        label="REST API"
                        value={agent.rest_available ? "Available" : "Unavailable"}
                    />
                )}
                {agent.powershell_available !== undefined && (
                    <Row
                        label="PowerShell"
                        value={agent.powershell_available ? "Available" : "Unavailable"}
                    />
                )}

                <SectionTitle>Database engine</SectionTitle>
                <Row label="Type" value={(db_detect.db_type ?? "unknown").toUpperCase()} />
                <Row label="psql" value={db_detect.psql_found ? "Found" : "Not found"} />
                <Row label="sqlcmd" value={db_detect.sqlcmd_found ? "Found" : "Not found"} />
                <Row
                    label="PostgreSQL :5432"
                    value={db_detect.pg_port ? "Listening" : "Not listening"}
                />
                <Row
                    label="SQL Server :1433"
                    value={db_detect.mssql_port ? "Listening" : "Not listening"}
                />
                {db_detect.error && <Row label="Detect error" value={db_detect.error} />}

                <SectionTitle>Live query (SELECT 1)</SectionTitle>
                <Row label="Result" value={db_query.success ? "Query succeeded" : "Query failed"} />
                {db_query.error && <Row label="Error" value={db_query.error} />}
                {db_query.output && <Row label="Output" value={db_query.output} />}
                {db_query.stderr && <Row label="stderr" value={db_query.stderr} />}
            </div>

            {recommendations.length > 0 && (
                <div style={{ marginTop: "0.5rem" }}>
                    <SectionTitle>Recommendations</SectionTitle>
                    <ul
                        style={{
                            margin: 0,
                            paddingLeft: "1.25rem",
                            color: "#c9d1d9",
                            fontSize: "0.85rem",
                        }}
                    >
                        {recommendations.map((rec, i) => (
                            <li key={i}>{rec}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}