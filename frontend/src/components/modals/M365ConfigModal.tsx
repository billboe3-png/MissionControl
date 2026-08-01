import { useState } from "react";
import LoadingButton from "../common/LoadingButton";
import {
    integrationsApi,
    IntegrationProfile,
} from "../../services/integrations";
import AgentSelector from "../common/AgentSelector";

interface M365ConfigModalProps {
    profile: IntegrationProfile | null;
    onSave: () => void;
    onCancel: () => void;
    onError: (message: string) => void;
}

export default function M365ConfigModal({
    profile,
    onSave,
    onCancel,
    onError,
}: M365ConfigModalProps) {
    const [name, setName] = useState(profile?.name ?? "Microsoft 365");
    const [tenantId, setTenantId] = useState(profile?.tenant_id ?? "");
    const [clientId, setClientId] = useState(profile?.client_id ?? "");
    const [clientSecret, setClientSecret] = useState("");
    const [authorityUrl, setAuthorityUrl] = useState(
        profile?.authority_url ?? "https://login.microsoftonline.com",
    );
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
                tenant_id: tenantId,
                client_id: clientId,
                authority_url: authorityUrl,
                timeout: parseInt(timeout, 10) || 30,
                agent_id: agentId || null,
            };
            if (clientSecret) payload.client_secret = clientSecret;

            if (isEditing) {
                await integrationsApi.update(profile!.id, payload);
            } else {
                await integrationsApi.create({
                    integration_type: "microsoft_365",
                    ...payload,
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
                    {isEditing ? "Configure Microsoft 365" : "Add Microsoft 365 Integration"}
                </h3>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="m365-name">Name</label>
                        <input
                            id="m365-name"
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
                        <label htmlFor="m365-tenant">Tenant ID</label>
                        <input
                            id="m365-tenant"
                            type="text"
                            className="form-input"
                            value={tenantId}
                            onChange={(e) => setTenantId(e.target.value)}
                            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                            required
                        />
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="m365-client-id">Client ID</label>
                            <input
                                id="m365-client-id"
                                type="text"
                                className="form-input"
                                value={clientId}
                                onChange={(e) => setClientId(e.target.value)}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="m365-client-secret">Client Secret</label>
                            <input
                                id="m365-client-secret"
                                type="password"
                                className="form-input"
                                value={clientSecret}
                                onChange={(e) => setClientSecret(e.target.value)}
                                placeholder={isEditing ? "Leave blank to keep existing" : ""}
                                required={!isEditing}
                            />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="m365-authority">Authority URL</label>
                            <input
                                id="m365-authority"
                                type="url"
                                className="form-input"
                                value={authorityUrl}
                                onChange={(e) => setAuthorityUrl(e.target.value)}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="m365-timeout">Timeout (sec)</label>
                            <input
                                id="m365-timeout"
                                type="number"
                                className="form-input"
                                value={timeout}
                                onChange={(e) => setTimeout_(e.target.value)}
                                min={1}
                                max={120}
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
