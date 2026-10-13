import { useState } from "react";
import PageHeader from "../common/PageHeader";
import LoadingButton from "../common/LoadingButton";
import { ServerSelector } from "./ServerSelector";
import VeeamDiagnosticsPanel from "./VeeamDiagnosticsPanel";
import { useVeeamServer } from "../../contexts/VeeamServerContext";
import { veeamApi, type VeeamServerDiagnostics } from "../../services/veeam";

interface VeeamPageShellProps {
    title: React.ReactNode;
    version?: string;
    onRefresh: () => void;
    refreshing?: boolean;
    children?: React.ReactNode;
}

export default function VeeamPageShell({
    title,
    version = "1.0",
    onRefresh,
    refreshing = false,
    children,
}: VeeamPageShellProps) {
    const { servers, selectedServerId } = useVeeamServer();
    const [diagnostics, setDiagnostics] = useState<VeeamServerDiagnostics | null>(null);
    const [diagnosing, setDiagnosing] = useState(false);
    const [diagnosticsError, setDiagnosticsError] = useState<string | null>(null);

    const serverName =
        servers.length > 0
            ? servers.find((s) => s.id === selectedServerId)?.name ?? "Veeam Server"
            : "Veeam Server";

    const runDiagnostics = async () => {
        if (selectedServerId == null) return;
        setDiagnosing(true);
        setDiagnostics(null);
        setDiagnosticsError(null);
        try {
            setDiagnostics(await veeamApi.diagnoseServer(selectedServerId));
        } catch (err) {
            setDiagnosticsError(err instanceof Error ? err.message : String(err));
        } finally {
            setDiagnosing(false);
        }
    };

    return (
        <>
            <PageHeader
                title={title}
                subtitle={`${serverName} v${version}`}
                actions={
                    <>
                        <LoadingButton
                            loading={diagnosing}
                            onClick={runDiagnostics}
                            disabled={selectedServerId == null}
                            className="btn btn-secondary"
                            title="Run diagnostics for the selected server"
                        >
                            Diagnose
                        </LoadingButton>
                        <LoadingButton
                            loading={refreshing}
                            onClick={onRefresh}
                            className="btn btn-secondary"
                            title="Refresh data"
                        >
                            Refresh
                        </LoadingButton>
                    </>
                }
            />
            <ServerSelector />
            {diagnosticsError && (
                <div
                    style={{
                        border: "1px solid #f85149",
                        background: "rgba(248,81,73,0.08)",
                        color: "#f85149",
                        borderRadius: "8px",
                        padding: "0.75rem 1rem",
                        marginBottom: "0.75rem",
                        fontSize: "0.85rem",
                    }}
                >
                    Diagnostics failed: {diagnosticsError}
                </div>
            )}
            {diagnostics && (
                <VeeamDiagnosticsPanel result={diagnostics} onClose={() => setDiagnostics(null)} />
            )}
            {children}
        </>
    );
}
