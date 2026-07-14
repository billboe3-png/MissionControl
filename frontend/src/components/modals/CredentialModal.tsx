import { useState } from "react";
import LoadingButton from "../common/LoadingButton";
import { credentialsApi, CredentialCreateInput, CredentialData } from "../../services/remote";

interface CredentialModalProps {
    credential?: CredentialData;
    onSave: () => void;
    onCancel: () => void;
    onError: (message: string) => void;
}

export default function CredentialModal({
    credential,
    onSave,
    onCancel,
    onError,
}: CredentialModalProps) {
    const [name, setName] = useState(credential?.name ?? "");
    const [authType, setAuthType] = useState(credential?.authentication_type ?? "password");
    const [username, setUsername] = useState(credential?.username ?? "");
    const [password, setPassword] = useState("");
    const [sshKey, setSshKey] = useState("");
    const [passphrase, setPassphrase] = useState("");
    const [description, setDescription] = useState(credential?.description ?? "");
    const [loading, setLoading] = useState(false);

    const isEditing = credential !== undefined;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const payload: CredentialCreateInput = {
                name,
                authentication_type: authType,
                username,
                password: password || undefined,
                ssh_key: sshKey || undefined,
                passphrase: passphrase || undefined,
                description: description || undefined,
            };

            if (isEditing) {
                await credentialsApi.update(credential.id, {
                    name,
                    authentication_type: authType,
                    username,
                    password: password || undefined,
                    ssh_key: sshKey || undefined,
                    passphrase: passphrase || undefined,
                    description: description || undefined,
                });
            } else {
                await credentialsApi.create(payload);
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
                    {isEditing ? "Edit Credential" : "New Credential"}
                </h3>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="cred-name">Name</label>
                        <input
                            id="cred-name"
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
                            <label htmlFor="cred-auth-type">Auth Type</label>
                            <select
                                id="cred-auth-type"
                                className="form-input"
                                value={authType}
                                onChange={(e) => setAuthType(e.target.value)}
                            >
                                <option value="password">Password</option>
                                <option value="ssh_key">SSH Key</option>
                                <option value="ntlm">NTLM</option>
                                <option value="basic">Basic</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label htmlFor="cred-username">Username</label>
                            <input
                                id="cred-username"
                                type="text"
                                className="form-input"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                                maxLength={200}
                            />
                        </div>
                    </div>

                    {(authType === "password" || authType === "ntlm" || authType === "basic") && (
                        <div className="form-group">
                            <label htmlFor="cred-password">Password</label>
                            <input
                                id="cred-password"
                                type="password"
                                className="form-input"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder={isEditing ? "Leave blank to keep existing" : ""}
                            />
                        </div>
                    )}

                    {authType === "ssh_key" && (
                        <>
                            <div className="form-group">
                                <label htmlFor="cred-ssh-key">SSH Private Key</label>
                                <textarea
                                    id="cred-ssh-key"
                                    className="form-input form-textarea"
                                    value={sshKey}
                                    onChange={(e) => setSshKey(e.target.value)}
                                    placeholder={isEditing ? "Leave blank to keep existing" : "Paste SSH private key content"}
                                    rows={4}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="cred-passphrase">Key Passphrase (optional)</label>
                                <input
                                    id="cred-passphrase"
                                    type="password"
                                    className="form-input"
                                    value={passphrase}
                                    onChange={(e) => setPassphrase(e.target.value)}
                                    placeholder={isEditing ? "Leave blank to keep existing" : ""}
                                />
                            </div>
                        </>
                    )}

                    <div className="form-group">
                        <label htmlFor="cred-description">Description</label>
                        <textarea
                            id="cred-description"
                            className="form-input form-textarea"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            maxLength={1000}
                            rows={2}
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
