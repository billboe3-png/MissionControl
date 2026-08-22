import { useState } from "react";
import LoadingButton from "../common/LoadingButton";
import {
    integrationsApi,
    IntegrationProfile,
} from "../../services/integrations";
import AgentSelector from "../common/AgentSelector";

interface ADConfigModalProps {
    profile: IntegrationProfile | null;
    onSave: () => void;
    onCancel: () => void;
    onError: (message: string) => void;
}

export default function ADConfigModal({
    profile,
    onSave,
    onCancel,
    onError,
}: ADConfigModalProps) {
    const [name, setName] = useState(profile?.name ?? "Active Directory");
    const [domain, setDomain] = useState(profile?.domain ?? "");
    const [baseDn, setBaseDn] = useState(profile?.base_dn ?? "");
    const [username, setUsername] = useState(profile?.username ?? "");
    const [password, setPassword] = useState("");
    const [useSsl, setUseSsl] = useState(profile?.use_ssl ?? true);
    const [timeout, setTimeout_] = useState(String(profile?.timeout ?? 30));
    const [agentId, setAgentId] = useState<number | null>(profile?.agent_id ?? null);
    const [loading, setLoading] = useState(false);

    const isEditing = profile !== null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const payload: Record<string, unknown> = {
                name,
                domain,
                base_dn: baseDn || undefined,
                username,
                use_ssl: useSsl,
                timeout: parseInt(timeout, 10) || 30,
                agent_id: agentId,
            };
            if (password) payload.password = password;

            if (isEditing) {
                await integrationsApi.update(profile!.id, payload);
            } else {
                await integrationsApi.create({
                    ...payload,
                    integration_type: "active_directory",
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
                    {isEditing ? "Configure Active Directory" : "Add Active Directory Integration"}
                </h3>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="ad-name">Name</label>
                        <input
                            id="ad-name"
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
                        <label htmlFor="ad-domain">Domain</label>
                        <input
                            id="ad-domain"
                            type="text"
                            className="form-input"
                            value={domain}
                            onChange={(e) => setDomain(e.target.value)}
                            placeholder="example.com"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="ad-basedn">Base DN (optional)</label>
                        <input
                            id="ad-basedn"
                            type="text"
                            className="form-input"
                            value={baseDn}
                            onChange={(e) => setBaseDn(e.target.value)}
                            placeholder="DC=corp,DC=example,DC=com"
                        />
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="ad-username">Username</label>
                            <input
                                id="ad-username"
                                type="text"
                                className="form-input"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="ad-password">Password</label>
                            <input
                                id="ad-password"
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
                            <label htmlFor="ad-timeout">Timeout (sec)</label>
                            <input
                                id="ad-timeout"
                                type="number"
                                className="form-input"
                                value={timeout}
                                onChange={(e) => setTimeout_(e.target.value)}
                                min={1}
                                max={120}
                            />
                        </div>
                        <div className="form-group form-group-inline">
                            <label htmlFor="ad-ssl">Use SSL</label>
                            <input
                                id="ad-ssl"
                                type="checkbox"
                                checked={useSsl}
                                onChange={(e) => setUseSsl(e.target.checked)}
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
