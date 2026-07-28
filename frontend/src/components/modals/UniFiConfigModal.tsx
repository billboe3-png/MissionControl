import { useState } from "react";
import LoadingButton from "../common/LoadingButton";
import {
    integrationsApi,
    IntegrationProfile,
} from "../../services/integrations";

interface UniFiConfigModalProps {
    profile: IntegrationProfile | null;
    onSave: () => void;
    onCancel: () => void;
    onError: (message: string) => void;
}

export default function UniFiConfigModal({
    profile,
    onSave,
    onCancel,
    onError,
}: UniFiConfigModalProps) {
    const [name, setName] = useState(profile?.name ?? "UniFi Network");
    const [apiKey, setApiKey] = useState("");
    const [verifySsl, setVerifySsl] = useState(profile?.verify_ssl ?? true);
    const [timeout, setTimeout_] = useState(String(profile?.timeout ?? 30));
    const [loading, setLoading] = useState(false);

    const isEditing = profile !== null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            if (isEditing) {
                await integrationsApi.update(profile.id, {
                    name,
                    password: apiKey || undefined,
                    verify_ssl: verifySsl,
                    timeout: parseInt(timeout, 10) || 30,
                });
            } else {
                await integrationsApi.create({
                    name,
                    integration_type: "unifi",
                    password: apiKey,
                    verify_ssl: verifySsl,
                    timeout: parseInt(timeout, 10) || 30,
                });
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
                    {isEditing ? "Configure UniFi" : "Add UniFi Integration"}
                </h3>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="uf-name">Name</label>
                        <input
                            id="uf-name"
                            type="text"
                            className="form-input"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                            maxLength={200}
                            autoFocus
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="uf-key">Site Manager API Key</label>
                        <input
                            id="uf-key"
                            type="password"
                            className="form-input"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            placeholder={isEditing ? "Leave blank to keep existing" : "Paste UniFi Site Manager API key"}
                            required={!isEditing}
                        />
                        <small className="form-help">
                            Generate at unifi.ui.com → Settings → API Keys. Grants
                            read-only access to your Site Manager org (sites, devices,
                            clients, alerts).
                        </small>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="uf-timeout">Timeout (sec)</label>
                            <input
                                id="uf-timeout"
                                type="number"
                                className="form-input"
                                value={timeout}
                                onChange={(e) => setTimeout_(e.target.value)}
                                min={1}
                                max={120}
                            />
                        </div>
                        <div className="form-group form-group-inline">
                            <label htmlFor="uf-ssl">Verify SSL</label>
                            <input
                                id="uf-ssl"
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
