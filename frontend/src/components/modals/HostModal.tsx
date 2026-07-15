import { useEffect, useState } from "react";
import LoadingButton from "../common/LoadingButton";
import { hostsApi, HostCreateInput, HostData, credentialsApi, CredentialData } from "../../services/remote";

interface HostModalProps {
    host?: HostData;
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
    const [credentialProfileId, setCredentialProfileId] = useState<string>(
        host?.credential_profile_id != null ? String(host.credential_profile_id) : ""
    );
    const [loading, setLoading] = useState(false);
    const [credentials, setCredentials] = useState<CredentialData[]>([]);

    const isEditing = host !== undefined;

    useEffect(() => {
        credentialsApi.list().then((data) => setCredentials(data.items)).catch(() => {});
    }, []);

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
                credential_profile_id: credentialProfileId ? Number(credentialProfileId) : null,
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
                        <select
                            id="host-os"
                            className="form-input"
                            value={os}
                            onChange={(e) => setOs(e.target.value)}
                        >
                            <option value="">Select OS…</option>
                            <optgroup label="Windows">
                                <option value="Windows Server 2016">Windows Server 2016</option>
                                <option value="Windows Server 2019">Windows Server 2019</option>
                                <option value="Windows Server 2022">Windows Server 2022</option>
                                <option value="Windows Server 2025">Windows Server 2025</option>
                                <option value="Windows 10">Windows 10</option>
                                <option value="Windows 11">Windows 11</option>
                            </optgroup>
                            <optgroup label="Linux">
                                <option value="Ubuntu 20.04">Ubuntu 20.04</option>
                                <option value="Ubuntu 22.04">Ubuntu 22.04</option>
                                <option value="Ubuntu 24.04">Ubuntu 24.04</option>
                                <option value="Debian 11">Debian 11</option>
                                <option value="Debian 12">Debian 12</option>
                                <option value="RHEL 8">RHEL 8</option>
                                <option value="RHEL 9">RHEL 9</option>
                                <option value="Rocky Linux 8">Rocky Linux 8</option>
                                <option value="Rocky Linux 9">Rocky Linux 9</option>
                                <option value="CentOS 7">CentOS 7</option>
                                <option value="AlmaLinux 8">AlmaLinux 8</option>
                                <option value="AlmaLinux 9">AlmaLinux 9</option>
                                <option value="SUSE 15">SUSE 15</option>
                                <option value="Amazon Linux 2">Amazon Linux 2</option>
                            </optgroup>
                            <optgroup label="Other">
                                <option value="Other">Other</option>
                            </optgroup>
                        </select>
                    </div>

                    <div className="form-group">
                        <label htmlFor="host-credential">Credential Profile</label>
                        <select
                            id="host-credential"
                            className="form-input"
                            value={credentialProfileId}
                            onChange={(e) => setCredentialProfileId(e.target.value)}
                        >
                            <option value="">None</option>
                            {credentials.map((c) => (
                                <option key={c.id} value={c.id}>
                                    {c.name} ({c.username})
                                </option>
                            ))}
                        </select>
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
