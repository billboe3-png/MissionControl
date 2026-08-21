import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import { useToast } from "../../contexts/ToastContext";
import { remoteApi, hostsApi, HostData } from "../../services/remote";
import { agentsApi, Agent } from "../../services/agents";

function stripAnsi(str: string): string {
    return str
        // eslint-disable-next-line no-control-regex
        .replace(/\x1b\[[0-9;]*[a-zA-Z]/g, "")
        // eslint-disable-next-line no-control-regex
        .replace(/\x1b\[\?[0-9]*[a-zA-Z]/g, "")
        // eslint-disable-next-line no-control-regex
        .replace(/\x1b\][^\x07]*\x07/g, "")
        // eslint-disable-next-line no-control-regex
        .replace(/\x1b[()][A-Z0-9]/g, "")
        // eslint-disable-next-line no-control-regex
        .replace(/\x1b[78]/g, "");
}

export default function ExecutePage() {
    const { showToast } = useToast();
    const [searchParams] = useSearchParams();
    const [hosts, setHosts] = useState<HostData[]>([]);
    const [agents, setAgents] = useState<Agent[]>([]);
    const [viaAgent, setViaAgent] = useState(true);
    const [selectedAgentId, setSelectedAgentId] = useState<number | "">("");
    const [selectedHostId, setSelectedHostId] = useState<number | "">("");
    const [command, setCommand] = useState(() => searchParams.get("command") ?? "");
    const [shell, setShell] = useState(() => searchParams.get("shell") ?? "");
    const [running, setRunning] = useState(false);
    const [exitCode, setExitCode] = useState<number | null>(null);
    const [success, setSuccess] = useState<boolean | null>(null);
    const [error, setError] = useState<string | null>(null);
    const stdoutRef = useRef<HTMLPreElement>(null);
    const stderrRef = useRef<HTMLPreElement>(null);
    const abortRef = useRef<AbortController | null>(null);

    useEffect(() => {
        hostsApi.list().then((data) => setHosts(data.items)).catch(() => {});
        agentsApi
            .list()
            .then((d) => setAgents(d.items.filter((a) => a.status === "online" && a.enabled)))
            .catch(() => {});
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
        if (viaAgent && !selectedAgentId) return;
        setRunning(true);
        setExitCode(null);
        setSuccess(null);
        setError(null);
        if (stdoutRef.current) stdoutRef.current.textContent = "";
        if (stderrRef.current) stderrRef.current.textContent = "";

        const abort = new AbortController();
        abortRef.current = abort;

        try {
            const stream = remoteApi.executeCommandStream({
                host_id: selectedHostId,
                command: command.trim(),
                shell: shell || undefined,
                agent_id: viaAgent && selectedAgentId ? selectedAgentId : undefined,
            }, abort.signal);

            for await (const chunk of stream) {
                if (abort.signal.aborted) break;
                if (chunk.type === "stdout" && chunk.data && stdoutRef.current) {
                    stdoutRef.current.textContent += stripAnsi(chunk.data);
                    stdoutRef.current.scrollTop = stdoutRef.current.scrollHeight;
                } else if (chunk.type === "stderr" && chunk.data && stderrRef.current) {
                    stderrRef.current.textContent += stripAnsi(chunk.data);
                    stderrRef.current.scrollTop = stderrRef.current.scrollHeight;
                } else if (chunk.type === "exit") {
                    const code = chunk.exit_code ?? -1;
                    setExitCode(code);
                    setSuccess(code === 0);
                    if (code === 130) {
                        showToast("Command cancelled", undefined);
                    } else {
                        showToast(code === 0 ? "Command completed" : `Command failed (exit ${code})`, code === 0 ? undefined : "error");
                    }
                } else if (chunk.type === "error") {
                    setError(chunk.message ?? "Unknown error");
                    showToast(chunk.message ?? "Unknown error", "error");
                }
            }
        } catch (e: unknown) {
            if (e instanceof DOMException && e.name === "AbortError") {
                setExitCode(130);
                setSuccess(false);
                showToast("Command cancelled", undefined);
            } else {
                const msg = e instanceof Error ? e.message : "Execution failed";
                setError(msg);
                showToast(msg, "error");
            }
        } finally {
            setRunning(false);
            abortRef.current = null;
        }
    }, [selectedHostId, command, shell, viaAgent, selectedAgentId, showToast]);

    const handleStop = useCallback(() => {
        abortRef.current?.abort();
    }, []);

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
                <div className="form-row">
                    <label className="form-label">Connection</label>
                    <select
                        className="form-select"
                        value={viaAgent ? "agent" : "direct"}
                        onChange={(e) => setViaAgent(e.target.value === "agent")}
                    >
                        <option value="direct">Direct (server → host)</option>
                        <option value="agent">Via agent relay</option>
                    </select>
                    {viaAgent && (
                        <select
                            className="form-select"
                            value={selectedAgentId}
                            onChange={(e) => setSelectedAgentId(Number(e.target.value) || "")}
                        >
                            <option value="">Select an agent…</option>
                            {agents.map((a) => (
                                <option key={a.id} value={a.id}>
                                    {a.name} ({a.hostname})
                                </option>
                            ))}
                        </select>
                    )}
                </div>
                <button
                    className="btn btn-primary"
                    onClick={running ? handleStop : handleExecute}
                    disabled={!running && (!selectedHostId || !command.trim() || (viaAgent && !selectedAgentId))}
                >
                    {running ? "Stop" : "Execute"}
                </button>
            </div>
            {(running || exitCode !== null || error) && (
                <div className="execute-result">
                    <h3>
                        Output{" "}
                        {exitCode !== null && (
                            <span className={success ? "text-success" : "text-error"}>
                                ({success ? "success" : "failed"}, exit {exitCode})
                            </span>
                        )}
                        {running && <span className="text-warning"> (running…)</span>}
                    </h3>
                    {error && <pre className="execute-stderr">{error}</pre>}
                    <pre
                        ref={stdoutRef}
                        className="execute-stdout"
                        style={{ minHeight: 80, whiteSpace: "pre-wrap", wordBreak: "break-all" }}
                    />
                    <pre
                        ref={stderrRef}
                        className="execute-stderr"
                        style={{ minHeight: 20, whiteSpace: "pre-wrap", wordBreak: "break-all" }}
                    />
                </div>
            )}
        </>
    );
}
