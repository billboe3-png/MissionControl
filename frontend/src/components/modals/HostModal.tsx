import { useState } from "react";
import LoadingButton from "../common/LoadingButton";
import { hostsApi, HostCreateInput } from "../../services/remote";
import { RemoteHost } from "../../types/dashboard";

interface HostModalProps {
    host?: RemoteHost;
    onSave: () => void;
    onCancel: () => void;
    onError: (message: string) => void;
}

export default function HostModal({
    host,
    onSave,
    onCancel,
    onError,
}: HostModalProps) {
    const [name, setName] = useState(host?.name ?? "");
    const [hostname, setHostname] = useState(host?.hostname ?? "");
    const [ipAddress, setIpAddress] = useState(host?.ip_address ?? "");
    const [os, setOs] = useState(host?.operating_system ?? "");
    const [connectionType, setConnectionType] = useState(host?.connection_type ?? "ssh");
    const [port, setPort] = useState(String(host?.port ?? 22));
    const [enabled, setEnabled] = useState(host?.enabled ?? true);
    const [loading, setLoading] = useState(false);

    const isEditing = host !== undefined;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const payload: HostCreateInput = {
                name,
                hostname,
                ip_address: ipAddress || undefined,
                operating_system: os || undefined,
                connection_type: connectionType,
                port: parseInt(port, 10) || 22,
                enabled,
            };

            if (isEditing) {
                await hostsApi.update(host.id, payload);
            } else {
                await hostsApi.create(payload);
            }
            onSave();
        } catch (err) {
            onError(err instanceof Error ? err.message : "Operation failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <h3 className="modal-title">
                    {isEditing ? "Edit Host" : "Add Host"}
                </h3>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="host-name">Name</label>
                        <input
                            id="host-name"
                            type="text"
                            className="form-input"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                            maxLength={200}
                            autoFocus
                        />
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="host-hostname">Hostname</label>
                            <input
                                id="host-hostname"
                                type="text"
                                className="form-input"
                                value={hostname}
                                onChange={(e) => setHostname(e.target.value)}
                                required
                                maxLength={500}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="host-ip">IP Address</label>
                            <input
                                id="host-ip"
                                type="text"
                                className="form-input"
                                value={ipAddress}
                                onChange={(e) => setIpAddress(e.target.value)}
                                maxLength={45}
                            />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="host-connection">Type</label>
                            <select
                                id="host-connection"
                                className="form-input"
                                value={connectionType}
                                onChange={(e) => setConnectionType(e.target.value)}
                            >
                                <option value="ssh">SSH</option>
                                <option value="winrm">WinRM</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label htmlFor="host-port">Port</label>
                            <input
                                id="host-port"
                                type="number"
                                className="form-input"
                                value={port}
                                onChange={(e) => setPort(e.target.value)}
                                min={1}
                                max={65535}
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="host-os">Operating System</label>
                        <input
                            id="host-os"
                            type="text"
                            className="form-input"
                            value={os}
                            onChange={(e) => setOs(e.target.value)}
                            placeholder="e.g. Ubuntu 22.04, Windows Server 2022"
                            maxLength={100}
                        />
                    </div>

                    <div className="form-group form-group-inline">
                        <label htmlFor="host-enabled">Enabled</label>
                        <input
                            id="host-enabled"
                            type="checkbox"
                            checked={enabled}
                            onChange={(e) => setEnabled(e.target.checked)}
                        />
                    </div>

                    <div className="modal-actions">
                        <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={onCancel}
                            disabled={loading}
                        >
                            Cancel
                        </button>
                        <LoadingButton type="submit" loading={loading}>
                            Save
                        </LoadingButton>
                    </div>
                </form>
            </div>
        </div>
    );
}
