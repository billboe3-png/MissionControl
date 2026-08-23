import { useState } from "react";
import LoadingButton from "../common/LoadingButton";
import {
    integrationsApi,
    IntegrationProfile,
} from "../../services/integrations";
import AgentSelector from "../common/AgentSelector";

interface HypervConfigModalProps {
    profile: IntegrationProfile | null;
    onSave: () => void;
    onCancel: () => void;
    onError: (message: string) => void;
}

export default function HypervConfigModal({
    profile,
    onSave,
    onCancel,
    onError,
}: HypervConfigModalProps) {
    const [name, setName] = useState(profile?.name ?? "Hyper-V Cluster");
    const [baseUrl, setBaseUrl] = useState(profile?.base_url ?? "");
    const [username, setUsername] = useState(profile?.username ?? "");
    const [password, setPassword] = useState("");
    const [transport, setTransport] = useState(profile?.domain ?? "winrm");
    const [timeout, setTimeout_] = useState(String(profile?.timeout ?? 30));
    const [verifySsl, setVerifySsl] = useState(profile?.verify_ssl ?? true);
    const [agentId, setAgentId] = useState<number | null>(profile?.agent_id ?? null);
    const [loading, setLoading] = useState(false);

    const isEditing = profile !== null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const payload: Record<string, unknown> = {
                name,
                base_url: baseUrl,
                username,
                domain: transport,
                timeout: parseInt(timeout, 10) || 30,
                verify_ssl: verifySsl,
                agent_id: agentId,
            };
            if (password) payload.password = password;

            if (isEditing) {
                await integrationsApi.update(profile!.id, payload);
            } else {
                await integrationsApi.create({
                    ...payload,
                    integration_type: "hyperv",
                } as Parameters<typeof integrationsApi.create>[0]);
            }
            onSave();
        } catch (err) {
            onError(err instanceof Error ? err.message : "Save failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <h3 className="modal-title">
                    {isEditing ? "Configure Hyper-V" : "Add Hyper-V Integration"}
                </h3>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="hv-name">Name</label>
                        <input
                            id="hv-name"
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

                    <div className="form-group">
                        <label htmlFor="hv-url">Hyper-V Host / Cluster</label>
                        <input
                            id="hv-url"
                            type="text"
                            className="form-input"
                            value={baseUrl}
                            onChange={(e) => setBaseUrl(e.target.value)}
                            placeholder="HV-HOST01.example.com or cluster name"
                            required
                        />
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="hv-username">Username</label>
                            <input
                                id="hv-username"
                                type="text"
                                className="form-input"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="DOMAIN\\username"
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="hv-password">Password</label>
                            <input
                                id="hv-password"
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
                            <label htmlFor="hv-transport">Transport</label>
                            <select
                                id="hv-transport"
                                className="form-input"
                                value={transport}
                                onChange={(e) => setTransport(e.target.value)}
                            >
                                <option value="winrm">WinRM (HTTP 5985)</option>
                                <option value="ssh">SSH (port 22)</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label htmlFor="hv-timeout">Timeout (sec)</label>
                            <input
                                id="hv-timeout"
                                type="number"
                                className="form-input"
                                value={timeout}
                                onChange={(e) => setTimeout_(e.target.value)}
                                min={1}
                                max={120}
                            />
                        </div>
                        <div className="form-group form-group-inline">
                            <label htmlFor="hv-ssl">Verify SSL</label>
                            <input
                                id="hv-ssl"
                                type="checkbox"
                                checked={verifySsl}
                                onChange={(e) => setVerifySsl(e.target.checked)}
                            />
                        </div>
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
                            {isEditing ? "Update" : "Create"}
                        </LoadingButton>
                    </div>
                </form>
            </div>
        </div>
    );
}
