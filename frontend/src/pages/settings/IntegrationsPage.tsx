import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import LoadingButton from "../../components/common/LoadingButton";
import StatusBadge from "../../components/common/StatusBadge";
import EmptyState from "../../components/common/EmptyState";
import {
    integrationsApi,
    IntegrationProfile,
} from "../../services/integrations";
import ZabbixConfigModal from "../../components/modals/ZabbixConfigModal";
import ADConfigModal from "../../components/modals/ADConfigModal";
import M365ConfigModal from "../../components/modals/M365ConfigModal";

type ConfigModalType = "zabbix" | "active_directory" | "microsoft_365" | null;

const INTEGRATION_DEFS: {
    type: ConfigModalType;
    label: string;
    icon: string;
    description: string;
}[] = [
    {
        type: "zabbix",
        label: "Zabbix",
        icon: "📡",
        description: "Zabbix monitoring — host health, problems, triggers and events.",
    },
    {
        type: "active_directory",
        label: "Active Directory",
        icon: "🏢",
        description: "LDAP/Active Directory — user lookup, group membership, organizational units.",
    },
    {
        type: "microsoft_365",
        label: "Microsoft 365",
        icon: "☁️",
        description: "Microsoft Graph — users, groups, licenses and tenant information.",
    },
];

export default function IntegrationsPage() {
    const [profiles, setProfiles] = useState<IntegrationProfile[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [modalType, setModalType] = useState<ConfigModalType>(null);
    const [editingProfile, setEditingProfile] = useState<IntegrationProfile | null>(null);
    const [testingId, setTestingId] = useState<number | null>(null);
    const [testResult, setTestResult] = useState<{
        id: number;
        success: boolean;
        message: string;
    } | null>(null);

    const load = async () => {
        try {
            const items = await integrationsApi.list();
            setProfiles(items);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, []);

    const getProfile = (type: string) =>
        profiles.find((p) => p.integration_type === type) ?? null;

    const handleToggle = async (profile: IntegrationProfile) => {
        try {
            if (profile.enabled) {
                await integrationsApi.disable(profile.id);
            } else {
                await integrationsApi.enable(profile.id);
            }
            await load();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Toggle failed");
        }
    };

    const handleTest = async (profile: IntegrationProfile) => {
        setTestingId(profile.id);
        setTestResult(null);
        try {
            const result = await integrationsApi.test(profile.id);
            setTestResult({
                id: profile.id,
                success: result.success,
                message: result.message ?? result.error ?? "Done",
            });
        } catch (e) {
            setTestResult({
                id: profile.id,
                success: false,
                message: e instanceof Error ? e.message : "Test failed",
            });
        } finally {
            setTestingId(null);
        }
    };

    const handleConfigure = (type: ConfigModalType) => {
        setEditingProfile(type ? getProfile(type) : null);
        setModalType(type);
    };

    const handleModalSave = async () => {
        setModalType(null);
        setEditingProfile(null);
        await load();
    };

    const handleDelete = async (profile: IntegrationProfile) => {
        if (!window.confirm(`Remove the ${profile.name} integration?`)) return;
        try {
            await integrationsApi.remove(profile.id);
            await load();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Delete failed");
        }
    };

    if (loading) return <div className="loading">Loading…</div>;

    return (
        <>
            <PageHeader
                title="Integrations"
                subtitle="Manage external platform connections"
            />

            {error && (
                <div className="error-banner">
                    {error}
                    <button className="btn btn-link" onClick={() => setError(null)}>
                        Dismiss
                    </button>
                </div>
            )}

            {profiles.length === 0 && !error && (
                <EmptyState
                    icon="🔌"
                    title="No integrations configured"
                    description="Choose a platform below to set up your first integration."
                />
            )}

            <div className="integrations-grid">
                {INTEGRATION_DEFS.map((def) => {
                    const profile = def.type ? getProfile(def.type) : null;
                    const connected =
                        profile?.enabled &&
                        profile.last_success !== null &&
                        profile.last_error === null;

                    return (
                        <div
                            key={def.type}
                            className={`integration-card ${profile?.enabled ? "enabled" : ""}`}
                        >
                            <div className="integration-card-header">
                                <span className="integration-card-icon">{def.icon}</span>
                                <div className="integration-card-title">
                                    <h3>{def.label}</h3>
                                    <p>{def.description}</p>
                                </div>
                            </div>

                            <div className="integration-card-status">
                                {!profile ? (
                                    <StatusBadge status="neutral" label="Not configured" />
                                ) : !profile.enabled ? (
                                    <StatusBadge status="neutral" label="Disabled" />
                                ) : connected ? (
                                    <StatusBadge status="healthy" label="Connected" />
                                ) : profile.last_error ? (
                                    <StatusBadge status="error" label="Error" />
                                ) : (
                                    <StatusBadge status="warning" label="Enabled (untested)" />
                                )}

                                {testResult && testResult.id === profile?.id && (
                                    <span
                                        className={`integration-test-result ${testResult.success ? "success" : "error"}`}
                                    >
                                        {testResult.message}
                                    </span>
                                )}
                            </div>

                            {profile && (
                                <div className="integration-card-meta">
                                    {profile.username && (
                                        <span>{profile.username}</span>
                                    )}
                                    {profile.base_url && (
                                        <span className="integration-meta-url">
                                            {profile.base_url}
                                        </span>
                                    )}
                                    {profile.last_test && (
                                        <span>
                                            Last tested:{" "}
                                            {new Date(profile.last_test).toLocaleString()}
                                        </span>
                                    )}
                                </div>
                            )}

                            <div className="integration-card-actions">
                                {profile ? (
                                    <>
                                        <LoadingButton
                                            loading={testingId === profile.id}
                                            className="btn btn-secondary btn-sm"
                                            onClick={() => handleTest(profile)}
                                        >
                                            Test
                                        </LoadingButton>
                                        <button
                                            className={`btn btn-sm ${profile.enabled ? "btn-warning" : "btn-primary"}`}
                                            onClick={() => handleToggle(profile)}
                                        >
                                            {profile.enabled ? "Disable" : "Enable"}
                                        </button>
                                        <button
                                            className="btn btn-secondary btn-sm"
                                            onClick={() => handleConfigure(def.type)}
                                        >
                                            Configure
                                        </button>
                                        <button
                                            className="btn btn-danger btn-sm"
                                            onClick={() => handleDelete(profile)}
                                        >
                                            Remove
                                        </button>
                                    </>
                                ) : (
                                    <button
                                        className="btn btn-primary btn-sm"
                                        onClick={() => handleConfigure(def.type)}
                                    >
                                        Configure
                                    </button>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {modalType === "zabbix" && (
                <ZabbixConfigModal
                    profile={editingProfile}
                    onSave={handleModalSave}
                    onCancel={() => {
                        setModalType(null);
                        setEditingProfile(null);
                    }}
                    onError={(msg) => setError(msg)}
                />
            )}
            {modalType === "active_directory" && (
                <ADConfigModal
                    profile={editingProfile}
                    onSave={handleModalSave}
                    onCancel={() => {
                        setModalType(null);
                        setEditingProfile(null);
                    }}
                    onError={(msg) => setError(msg)}
                />
            )}
            {modalType === "microsoft_365" && (
                <M365ConfigModal
                    profile={editingProfile}
                    onSave={handleModalSave}
                    onCancel={() => {
                        setModalType(null);
                        setEditingProfile(null);
                    }}
                    onError={(msg) => setError(msg)}
                />
            )}
        </>
    );
}
