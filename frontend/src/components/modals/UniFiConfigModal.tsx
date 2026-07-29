import { useState } from "react";
import LoadingButton from "../common/LoadingButton";
import {
    integrationsApi,
    IntegrationProfile,
} from "../../services/integrations";

const CLOUD_URL = "https://api.ui.com";

function detectType(base_url: string | null | undefined): "cloud" | "local" {
    if (!base_url || base_url === CLOUD_URL || base_url === CLOUD_URL + "/") {
        return "cloud";
    }
    return "local";
}

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
    const [connectionType, setConnectionType] = useState<"cloud" | "local">(
        detectType(profile?.base_url)
    );
    const [url, setUrl] = useState(
        connectionType === "cloud" ? CLOUD_URL : (profile?.base_url ?? "")
    );
    const [verifySsl, setVerifySsl] = useState(profile?.verify_ssl ?? true);
    const [timeout, setTimeout_] = useState(String(profile?.timeout ?? 30));
    const [loading, setLoading] = useState(false);

    const isEditing = profile !== null;

    const handleTypeChange = (type: "cloud" | "local") => {
        setConnectionType(type);
        if (type === "cloud") {
            setUrl(CLOUD_URL);
        } else {
            setUrl(profile?.base_url && profile.base_url !== CLOUD_URL && profile.base_url !== CLOUD_URL + "/"
                ? profile.base_url
                : "");
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (connectionType === "local" && !url.trim()) {
            onError("Controller URL is required for local connections.");
            return;
        }

        setLoading(true);

        try {
            const base_url: string = connectionType === "cloud" ? CLOUD_URL : url.trim();
            if (isEditing) {
                await integrationsApi.update(profile.id, {
                    name,
                    password: apiKey || undefined,
                    base_url,
                    verify_ssl: verifySsl,
                    timeout: parseInt(timeout, 10) || 30,
                });
            } else {
                await integrationsApi.create({
                    name,
                    integration_type: "unifi",
                    password: apiKey,
                    base_url,
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
                        <label htmlFor="uf-type">Connection Type</label>
                        <select
                            id="uf-type"
                            className="form-input"
                            value={connectionType}
                            onChange={(e) => handleTypeChange(e.target.value as "cloud" | "local")}
                        >
                            <option value="cloud">Cloud (api.ui.com)</option>
                            <option value="local">Local Controller</option>
                        </select>
                        <small className="form-help">
                            {connectionType === "cloud"
                                ? "Connect via the UniFi cloud API at api.ui.com using your Site Manager API key."
                                : "Connect to a local UniFi controller (UDM, Cloud Key, or self-hosted)."}
                        </small>
                    </div>

                    <div className="form-group">
                        <label htmlFor="uf-url">
                            Controller URL {connectionType === "local" ? "*" : ""}
                        </label>
                        <input
                            id="uf-url"
                            type="url"
                            className="form-input"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            placeholder={
                                connectionType === "cloud"
                                    ? "https://unifi.ui.com"
                                    : "https://192.168.1.1:8443"
                            }
                            required={connectionType === "local"}
                            disabled={connectionType === "cloud"}
                            maxLength={500}
                        />
                        {connectionType === "cloud" && (
                            <small className="form-help">
                                Uses the official UniFi cloud API at api.ui.com. Generate an API
                                key at unifi.ui.com → Settings → API Keys.
                            </small>
                        )}
                    </div>

                    <div className="form-group">
                        <label htmlFor="uf-key">API Key</label>
                        <input
                            id="uf-key"
                            type="password"
                            className="form-input"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            placeholder={isEditing ? "Leave blank to keep existing" : "Paste UniFi API key"}
                            required={!isEditing}
                        />
                        <small className="form-help">
                            {connectionType === "cloud"
                                ? "Generate at unifi.ui.com → Settings → API Keys."
                                : "API key from your local controller's Settings → Integrations."}
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
