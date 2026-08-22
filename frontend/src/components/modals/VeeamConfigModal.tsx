import { useState } from "react";
import LoadingButton from "../common/LoadingButton";
import {
    integrationsApi,
    IntegrationProfile,
} from "../../services/integrations";
import AgentSelector from "../common/AgentSelector";

interface VeeamConfigModalProps {
    profile: IntegrationProfile | null;
    onSave: () => void;
    onCancel: () => void;
    onError: (message: string) => void;
}

export default function VeeamConfigModal({
    profile,
    onSave,
    onCancel,
    onError,
}: VeeamConfigModalProps) {
    const isEditing = profile !== null;
    const isCommunityEdition = isEditing && !profile?.base_url && Boolean(profile?.ssh_host);

    const [edition, setEdition] = useState<"enterprise" | "community">(
        isCommunityEdition ? "community" : "enterprise"
    );

    const [name, setName] = useState(profile?.name ?? "Veeam B&R Server");
    const [baseUrl, setBaseUrl] = useState(profile?.base_url ?? "");
    const [username, setUsername] = useState(profile?.username ?? "");
    const [password, setPassword] = useState("");
    const [timeout, setTimeout_] = useState(String(profile?.timeout ?? 30));
    const [verifySsl, setVerifySsl] = useState(profile?.verify_ssl ?? true);
    const [dataSource, setDataSource] = useState(profile?.data_source ?? "both");
    const [agentId, setAgentId] = useState<number | null>(profile?.agent_id ?? null);

    const [sshHost, setSshHost] = useState(profile?.ssh_host ?? "");
    const [sshPort, setSshPort] = useState(String(profile?.ssh_port ?? 22));
    const [sshUsername, setSshUsername] = useState(profile?.ssh_username ?? "");
    const [sshPassword, setSshPassword] = useState("");

    const [loading, setLoading] = useState(false);

    const isEnterprise = edition === "enterprise";
    const needsSsh = isEnterprise ? (dataSource === "ssh" || dataSource === "both") : true;
    const needsApi = isEnterprise && (dataSource === "api" || dataSource === "both");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const payload: Record<string, unknown> = {
                name,
                timeout: parseInt(timeout, 10) || 30,
                agent_id: agentId,
            };

            if (isEnterprise) {
                payload.base_url = baseUrl;
                payload.username = username;
                payload.verify_ssl = verifySsl;
                payload.data_source = dataSource;
                if (password) payload.password = password;
                if (needsSsh) {
                    payload.ssh_host = sshHost;
                    payload.ssh_port = parseInt(sshPort, 10) || 22;
                    payload.ssh_username = sshUsername;
                    if (sshPassword) payload.ssh_password = sshPassword;
                } else {
                    payload.ssh_host = "";
                    payload.ssh_username = "";
                }
            } else {
                // Community Edition: no base_url, use SSH fields
                payload.base_url = "";
                payload.username = sshUsername;
                payload.ssh_host = sshHost;
                payload.ssh_port = parseInt(sshPort, 10) || 22;
                payload.ssh_username = sshUsername;
                if (sshPassword) payload.ssh_password = sshPassword;
            }

            if (isEditing) {
                await integrationsApi.update(profile!.id, payload);
            } else {
                await integrationsApi.create({
                    ...payload,
                    integration_type: "veeam",
                } as Parameters<typeof integrationsApi.create>[0]);
            }
            onSave();
        } catch (err) {
            onError(err instanceof Error ? err.message : "Save failed");
        } finally {
            setLoading(false);
        }
    };

    const hasSshConfig = Boolean(profile?.ssh_host);

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <h3 className="modal-title">
                    {isEditing ? "Configure Veeam B&R" : "Add Veeam Integration"}
                </h3>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Edition</label>
                        <div className="radio-group" style={{ display: "flex", gap: "1.5rem", marginTop: "0.35rem" }}>
                            <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", cursor: "pointer", fontSize: "0.85rem" }}>
                                <input
                                    type="radio"
                                    name="edition"
                                    value="enterprise"
                                    checked={isEnterprise}
                                    onChange={() => setEdition("enterprise")}
                                />
                                Enterprise (REST API)
                            </label>
                            <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", cursor: "pointer", fontSize: "0.85rem" }}>
                                <input
                                    type="radio"
                                    name="edition"
                                    value="community"
                                    checked={!isEnterprise}
                                    onChange={() => setEdition("community")}
                                />
                                Community Edition (PowerShell over SSH)
                            </label>
                        </div>
                        <div style={{ fontSize: "0.75rem", color: "#8b949e", marginTop: "0.25rem" }}>
                            {!isEnterprise
                                ? "Runs Veeam PowerShell cmdlets remotely via SSH. No REST API required."
                                : "Connects to the Veeam REST API (v1). Optionally add SSH for transfer statistics."}
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="vm-name">Name</label>
                        <input
                            id="vm-name"
                            type="text"
                            className="form-input"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                            maxLength={200}
                            autoFocus
                        />
                    </div>

                    <AgentSelector value={agentId} onChange={setAgentId} />

                    {isEnterprise && (
                        <>
                            <div className="form-group">
                                <label>Data Source</label>
                                <div className="radio-group" style={{ display: "flex", gap: "1.5rem", marginTop: "0.35rem" }}>
                                    <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", cursor: "pointer", fontSize: "0.85rem" }}>
                                        <input
                                            type="radio"
                                            name="data_source"
                                            value="api"
                                            checked={dataSource === "api"}
                                            onChange={() => setDataSource("api")}
                                        />
                                        API only
                                    </label>
                                    <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", cursor: "pointer", fontSize: "0.85rem" }}>
                                        <input
                                            type="radio"
                                            name="data_source"
                                            value="ssh"
                                            checked={dataSource === "ssh"}
                                            onChange={() => setDataSource("ssh")}
                                        />
                                        SSH only
                                    </label>
                                    <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", cursor: "pointer", fontSize: "0.85rem" }}>
                                        <input
                                            type="radio"
                                            name="data_source"
                                            value="both"
                                            checked={dataSource === "both"}
                                            onChange={() => setDataSource("both")}
                                        />
                                        Both (Recommended)
                                    </label>
                                </div>
                                <div style={{ fontSize: "0.75rem", color: "#8b949e", marginTop: "0.25rem" }}>
                                    {dataSource === "api" && "REST API only - jobs, sessions, repositories. No transfer statistics."}
                                    {dataSource === "ssh" && "SSH + PostgreSQL direct query - full session and transfer data. Requires SSH access to Veeam server."}
                                    {dataSource === "both" && "REST API for metadata + SSH for transfer statistics. Recommended for full visibility."}
                                </div>
                            </div>

                            <div className="form-group">
                                <label htmlFor="vm-url">Server URL</label>
                                <input
                                    id="vm-url"
                                    type="url"
                                    className="form-input"
                                    value={baseUrl}
                                    onChange={(e) => setBaseUrl(e.target.value)}
                                    placeholder="https://veeam.example.com:9419"
                                    required
                                />
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="vm-username">Username</label>
                                    <input
                                        id="vm-username"
                                        type="text"
                                        className="form-input"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        placeholder="DOMAIN\\username or username"
                                        required
                                    />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="vm-password">Password</label>
                                    <input
                                        id="vm-password"
                                        type="password"
                                        className="form-input"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder={isEditing ? "Leave blank to keep existing" : ""}
                                        required={!isEditing}
                                    />
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="vm-timeout">Timeout (sec)</label>
                                    <input
                                        id="vm-timeout"
                                        type="number"
                                        className="form-input"
                                        value={timeout}
                                        onChange={(e) => setTimeout_(e.target.value)}
                                        min={1}
                                        max={120}
                                    />
                                </div>
                                <div className="form-group form-group-inline">
                                    <label htmlFor="vm-ssl">Verify SSL</label>
                                    <input
                                        id="vm-ssl"
                                        type="checkbox"
                                        checked={verifySsl}
                                        onChange={(e) => setVerifySsl(e.target.checked)}
                                    />
                                </div>
                            </div>
                        </>
                    )}

                    {needsSsh && (
                        <>
                            <div className="form-group" style={{ marginTop: isEnterprise ? "0.5rem" : 0 }}>
                                <label>{isEnterprise ? "SSH Connection" : "Connection (SSH)"}</label>
                                <div style={{ fontSize: "0.75rem", color: "#8b949e", marginTop: "0.25rem" }}>
                                    {isEnterprise
                                        ? "Direct SSH access to the Veeam server for PostgreSQL database queries (transfer statistics)"
                                        : "SSH connection to the Veeam server for running PowerShell cmdlets remotely"}
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="vm-ssh-host">SSH Host</label>
                                    <input
                                        id="vm-ssh-host"
                                        type="text"
                                        className="form-input"
                                        value={sshHost}
                                        onChange={(e) => setSshHost(e.target.value)}
                                        placeholder="192.168.1.100"
                                        required
                                    />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="vm-ssh-port">SSH Port</label>
                                    <input
                                        id="vm-ssh-port"
                                        type="number"
                                        className="form-input"
                                        value={sshPort}
                                        onChange={(e) => setSshPort(e.target.value)}
                                        min={1}
                                        max={65535}
                                    />
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="vm-ssh-username">SSH Username</label>
                                    <input
                                        id="vm-ssh-username"
                                        type="text"
                                        className="form-input"
                                        value={sshUsername}
                                        onChange={(e) => setSshUsername(e.target.value)}
                                        placeholder="DOMAIN\username"
                                        required
                                    />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="vm-ssh-password">SSH Password</label>
                                    <input
                                        id="vm-ssh-password"
                                        type="password"
                                        className="form-input"
                                        value={sshPassword}
                                        onChange={(e) => setSshPassword(e.target.value)}
                                        placeholder={isEditing && hasSshConfig ? "Leave blank to keep existing" : ""}
                                        required={!isEditing}
                                    />
                                </div>
                            </div>
                        </>
                    )}

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
                            {isEditing ? "Update" : "Create"}
                        </LoadingButton>
                    </div>
                </form>
            </div>
        </div>
    );
}
