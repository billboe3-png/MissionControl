import { useState } from "react";
import LoadingButton from "../common/LoadingButton";
import {
    integrationsApi,
    IntegrationProfile,
} from "../../services/integrations";

interface ProxmoxConfigModalProps {
    profile: IntegrationProfile | null;
    onSave: () => void;
    onCancel: () => void;
    onError: (message: string) => void;
}

export default function ProxmoxConfigModal({
    profile,
    onSave,
    onCancel,
    onError,
}: ProxmoxConfigModalProps) {
    const [name, setName] = useState(profile?.name ?? "Proxmox Cluster");
    const [baseUrl, setBaseUrl] = useState(profile?.base_url ?? "");
    const [username, setUsername] = useState(profile?.username ?? "");
    const [password, setPassword] = useState("");
    const [timeout, setTimeout_] = useState(String(profile?.timeout ?? 30));
    const [verifySsl, setVerifySsl] = useState(profile?.verify_ssl ?? true);
    const [loading, setLoading] = useState(false);

    const isEditing = profile !== null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            if (isEditing) {
                await integrationsApi.update(profile.id, {
                    name,
                    base_url: baseUrl,
                    username,
                    password: password || undefined,
                    timeout: parseInt(timeout, 10) || 30,
                    verify_ssl: verifySsl,
                });
            } else {
                await integrationsApi.create({
                    name,
                    integration_type: "proxmox",
                    base_url: baseUrl,
                    username,
                    password,
                    timeout: parseInt(timeout, 10) || 30,
                    verify_ssl: verifySsl,
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
                    {isEditing ? "Configure Proxmox" : "Add Proxmox Integration"}
                </h3>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="pm-name">Name</label>
                        <input
                            id="pm-name"
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
                        <label htmlFor="pm-url">Server URL</label>
                        <input
                            id="pm-url"
                            type="url"
                            className="form-input"
                            value={baseUrl}
                            onChange={(e) => setBaseUrl(e.target.value)}
                            placeholder="https://pve.example.com:8006"
                            required
                        />
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="pm-username">API Token ID</label>
                            <input
                                id="pm-username"
                                type="text"
                                className="form-input"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="user@pve!tokenname"
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="pm-password">API Token Secret</label>
                            <input
                                id="pm-password"
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
                            <label htmlFor="pm-timeout">Timeout (sec)</label>
                            <input
                                id="pm-timeout"
                                type="number"
                                className="form-input"
                                value={timeout}
                                onChange={(e) => setTimeout_(e.target.value)}
                                min={1}
                                max={120}
                            />
                        </div>
                        <div className="form-group form-group-inline">
                            <label htmlFor="pm-ssl">Verify SSL</label>
                            <input
                                id="pm-ssl"
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
