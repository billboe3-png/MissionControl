import { useState } from "react";
import LoadingButton from "../common/LoadingButton";
import { remoteApi, ExecuteCommandResponse } from "../../services/remote";
import { RemoteHost } from "../../types/dashboard";

interface ExecuteCommandModalProps {
    host: RemoteHost;
    onExecute: (result: ExecuteCommandResponse) => void;
    onCancel: () => void;
    onError: (message: string) => void;
}

export default function ExecuteCommandModal({
    host,
    onExecute,
    onCancel,
    onError,
}: ExecuteCommandModalProps) {
    const [command, setCommand] = useState("");
    const [shell, setShell] = useState(
        host.connection_type === "winrm" ? "powershell" : "bash",
    );
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ExecuteCommandResponse | null>(null);
    const [copied, setCopied] = useState(false);

    const handleExecute = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await remoteApi.executeCommand({
                host_id: host.id,
                command,
                shell,
            });
            setResult(response);
            onExecute(response);
        } catch (err) {
            onError(err instanceof Error ? err.message : "Execution failed");
        } finally {
            setLoading(false);
        }
    };

    const handleCopyOutput = () => {
        if (!result) return;
        const text = result.stdout || result.stderr || "No output";
        navigator.clipboard.writeText(text).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        });
    };

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div
                className="modal-content modal-content-wide"
                onClick={(e) => e.stopPropagation()}
            >
                <h3 className="modal-title">
                    Execute Command — {host.name}
                </h3>

                <form onSubmit={handleExecute}>
                    <div className="form-row">
                        <div className="form-group form-group-grow">
                            <label htmlFor="exec-command">Command</label>
                            <input
                                id="exec-command"
                                type="text"
                                className="form-input"
                                value={command}
                                onChange={(e) => setCommand(e.target.value)}
                                required
                                autoFocus
                                placeholder={
                                    host.connection_type === "winrm"
                                        ? "Get-Process"
                                        : "hostname"
                                }
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="exec-shell">Shell</label>
                            <select
                                id="exec-shell"
                                className="form-input"
                                value={shell}
                                onChange={(e) => setShell(e.target.value)}
                            >
                                <option value="bash">Bash</option>
                                <option value="powershell">PowerShell</option>
                                <option value="cmd">CMD</option>
                            </select>
                        </div>
                    </div>

                    <div className="modal-actions">
                        <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={onCancel}
                            disabled={loading}
                        >
                            Close
                        </button>
                        <LoadingButton type="submit" loading={loading}>
                            Execute
                        </LoadingButton>
                    </div>
                </form>

                {result && (
                    <div className="command-output">
                        <div className="command-output-header">
                            <span>
                                Exit code:{" "}
                                <span className={result.success ? "text-success" : "text-error"}>
                                    {result.exit_code}
                                </span>
                                {" "}({result.duration_ms}ms)
                            </span>
                            <button
                                type="button"
                                className="btn btn-sm btn-ghost"
                                onClick={handleCopyOutput}
                            >
                                {copied ? "Copied" : "Copy"}
                            </button>
                        </div>
                        <pre className="command-output-pre">
                            {result.stdout || "(no stdout)"}
                        </pre>
                        {result.stderr && (
                            <pre className="command-output-pre command-output-stderr">
                                {result.stderr}
                            </pre>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
