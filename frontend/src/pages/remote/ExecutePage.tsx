import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import { useToast } from "../../contexts/ToastContext";
import {
    remoteApi,
    hostsApi,
    HostData,
    ExecuteCommandResponse,
} from "../../services/remote";

export default function ExecutePage() {
    const { showToast } = useToast();
    const [searchParams] = useSearchParams();
    const [hosts, setHosts] = useState<HostData[]>([]);
    const [selectedHostId, setSelectedHostId] = useState<number | "">("");
    const [command, setCommand] = useState(() => searchParams.get("command") ?? "");
    const [shell, setShell] = useState(() => searchParams.get("shell") ?? "");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ExecuteCommandResponse | null>(null);

    useEffect(() => {
        hostsApi.list().then((data) => setHosts(data.items)).catch(() => {});
    }, []);

    useEffect(() => {
        if (!selectedHostId) return;
        const host = hosts.find((h) => h.id === selectedHostId);
        if (!host) return;
        const os = (host.operating_system ?? "").toLowerCase();
        setShell(os.includes("windows") ? "powershell" : "bash");
    }, [selectedHostId, hosts]);

    const handleExecute = useCallback(async () => {
        if (!selectedHostId || !command.trim()) return;
        try {
            setLoading(true);
            setResult(null);
            const res = await remoteApi.executeCommand({
                host_id: selectedHostId,
                command: command.trim(),
                shell: shell || undefined,
            });
            setResult(res);
            if (res.success) {
                showToast("Command executed successfully");
            } else {
                showToast("Command failed", "error");
            }
        } catch (e: unknown) {
            showToast(e instanceof Error ? e.message : "Execution failed", "error");
        } finally {
            setLoading(false);
        }
    }, [selectedHostId, command, shell, showToast]);

    return (
        <>
            <PageHeader
                title="Execute Command"
                subtitle="Run a command on a remote host"
            />
            <div className="execute-form">
                <div className="form-row">
                    <label className="form-label">Host</label>
                    <select
                        className="form-select"
                        value={selectedHostId}
                        onChange={(e) => setSelectedHostId(Number(e.target.value) || "")}
                    >
                        <option value="">Select a host…</option>
                        {hosts.map((h) => (
                            <option key={h.id} value={h.id}>
                                {h.name} ({h.hostname})
                            </option>
                        ))}
                    </select>
                </div>
                <div className="form-row">
                    <label className="form-label">Command</label>
                    <input
                        className="form-input"
                        type="text"
                        placeholder="e.g. uptime"
                        value={command}
                        onChange={(e) => setCommand(e.target.value)}
                    />
                </div>
                <div className="form-row">
                    <label className="form-label">Shell</label>
                    <select
                        className="form-select"
                        value={shell}
                        onChange={(e) => setShell(e.target.value)}
                    >
                        <option value="">Default</option>
                        <option value="bash">Bash</option>
                        <option value="powershell">PowerShell</option>
                        <option value="cmd">CMD</option>
                    </select>
                </div>
                <button
                    className="btn btn-primary"
                    onClick={handleExecute}
                    disabled={loading || !selectedHostId || !command.trim()}
                >
                    {loading ? "Executing…" : "Execute"}
                </button>
            </div>
            {result && (
                <div className="execute-result">
                    <h3>
                        Result{" "}
                        <span className={result.success ? "text-success" : "text-error"}>
                            ({result.success ? "success" : "failed"}, exit {result.exit_code}, {result.duration_ms}ms)
                        </span>
                    </h3>
                    {result.stdout && (
                        <pre className="execute-stdout">{result.stdout}</pre>
                    )}
                    {result.stderr && (
                        <pre className="execute-stderr">{result.stderr}</pre>
                    )}
                </div>
            )}
        </>
    );
}
