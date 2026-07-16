import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { useToast } from "../../contexts/ToastContext";
import {
    automationApi,
    PlaybookData,
    PlaybookStepData,
    PlaybookVariableData,
} from "../../services/automation";

export default function PlaybookDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { showToast } = useToast();
    const [playbook, setPlaybook] = useState<PlaybookData | null>(null);
    const [steps, setSteps] = useState<PlaybookStepData[]>([]);
    const [variables, setVariables] = useState<PlaybookVariableData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [executing, setExecuting] = useState(false);
    const [dryRunning, setDryRunning] = useState(false);

    const loadData = useCallback(async () => {
        if (!id) return;
        try {
            setLoading(true);
            setError(null);
            const [p, s, v] = await Promise.all([
                automationApi.getPlaybook(Number(id)),
                automationApi.listSteps(Number(id)),
                automationApi.listVariables(Number(id)),
            ]);
            setPlaybook(p);
            setSteps(s.items);
            setVariables(v.items);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to load playbook");
        } finally {
            setLoading(false);
        }
    }, [id]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleExecute = async (mode: string) => {
        if (!id) return;
        try {
            if (mode === "dry_run") setDryRunning(true);
            else setExecuting(true);

            await automationApi.executePlaybook(Number(id), {
                mode,
                triggered_by: "ui_user",
            });
            showToast(`Playbook ${mode === "dry_run" ? "dry run" : "execution"} started`, "success");
            loadData();
        } catch (e: unknown) {
            showToast(e instanceof Error ? e.message : "Execution failed", "error");
        } finally {
            setExecuting(false);
            setDryRunning(false);
        }
    };

    const handleDeleteStep = async (stepId: number) => {
        if (!window.confirm("Delete this step?")) return;
        try {
            await automationApi.deleteStep(stepId);
            showToast("Step deleted", "success");
            loadData();
        } catch (e: unknown) {
            showToast(e instanceof Error ? e.message : "Delete failed", "error");
        }
    };

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;
    if (!playbook) return <div className="error-banner">Playbook not found</div>;

    return (
        <>
            <PageHeader
                title={playbook.name}
                subtitle={`v${playbook.version} · ${playbook.description ?? "No description"}`}
                actions={
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                        <button
                            className="btn btn-secondary"
                            onClick={() => handleExecute("dry_run")}
                            disabled={dryRunning || executing}
                        >
                            {dryRunning ? "Running…" : "Dry Run"}
                        </button>
                        <button
                            className="btn btn-primary"
                            onClick={() => handleExecute("live")}
                            disabled={executing || dryRunning}
                        >
                            {executing ? "Executing…" : "Execute"}
                        </button>
                        <button
                            className="btn btn-danger"
                            onClick={() => { if (id) { automationApi.deletePlaybook(Number(id)); navigate("/automation/playbooks"); } }}
                        >
                            Delete
                        </button>
                    </div>
                }
            />

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
                <div className="stat-card">
                    <div className="stat-label">Status</div>
                    <StatusBadge status={playbook.enabled ? "healthy" : "neutral"} label={playbook.enabled ? "Active" : "Disabled"} />
                </div>
                <div className="stat-card">
                    <div className="stat-label">Approval</div>
                    <StatusBadge status={playbook.requires_approval ? "warning" : "neutral"} label={playbook.requires_approval ? "Required" : "None"} />
                </div>
                <div className="stat-card">
                    <div className="stat-label">Auto-Rollback</div>
                    <StatusBadge status={playbook.auto_rollback ? "info" : "neutral"} label={playbook.auto_rollback ? "Enabled" : "Disabled"} />
                </div>
                <div className="stat-card">
                    <div className="stat-label">Timeout</div>
                    <span>{playbook.timeout_seconds}s</span>
                </div>
            </div>

            <div className="card" style={{ marginBottom: "1.5rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                    <h3 className="card-title" style={{ margin: 0 }}>Steps ({steps.length})</h3>
                    <button
                        className="btn btn-primary btn-sm"
                        onClick={() => navigate(`/automation/playbooks/${id}/steps/new`)}
                    >
                        + Add Step
                    </button>
                </div>
                {steps.length === 0 ? (
                    <p className="text-muted">No steps defined. Add steps to build your playbook.</p>
                ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                        {steps.map((step) => (
                            <div
                                key={step.id}
                                style={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                    alignItems: "center",
                                    padding: "0.75rem 1rem",
                                    background: "var(--surface)",
                                    borderRadius: "8px",
                                }}
                            >
                                <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                                    <span style={{ fontWeight: 700, color: "var(--primary)", minWidth: "2rem" }}>
                                        #{step.step_order}
                                    </span>
                                    <div>
                                        <div style={{ fontWeight: 600 }}>{step.name}</div>
                                        <code style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                                            {step.command.slice(0, 80)}{step.command.length > 80 ? "…" : ""}
                                        </code>
                                    </div>
                                </div>
                                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                                    <StatusBadge status="info" label={step.provider} />
                                    <StatusBadge status="neutral" label={step.step_type} />
                                    <button
                                        className="btn btn-danger btn-sm"
                                        onClick={() => handleDeleteStep(step.id)}
                                    >
                                        ×
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div className="card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                    <h3 className="card-title" style={{ margin: 0 }}>Variables ({variables.length})</h3>
                </div>
                {variables.length === 0 ? (
                    <p className="text-muted">No variables defined.</p>
                ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                        {variables.map((v) => (
                            <div
                                key={v.id}
                                style={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                    padding: "0.5rem 1rem",
                                    background: "var(--surface)",
                                    borderRadius: "8px",
                                }}
                            >
                                <div>
                                    <span style={{ fontWeight: 600 }}>{v.name}</span>
                                    <span className="text-muted" style={{ marginLeft: "0.5rem" }}>
                                        ({v.variable_type})
                                    </span>
                                </div>
                                <div>
                                    {v.sensitive ? (
                                        <span className="text-muted">•••••</span>
                                    ) : (
                                        <code>{v.value ?? v.default_value ?? "—"}</code>
                                    )}
                                    {v.required && (
                                        <StatusBadge status="warning" label="Required" />
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </>
    );
}
