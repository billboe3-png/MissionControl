import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import LoadingButton from "../../components/common/LoadingButton";
import StatusBadge from "../../components/common/StatusBadge";
import EmptyState from "../../components/common/EmptyState";
import {
    integrationsApi,
    IntegrationProfile,
} from "../../services/integrations";
import type { Agent, AgentListResponse } from "../../services/agents";
import { agentsApi } from "../../services/agents";
import ZabbixConfigModal from "../../components/modals/ZabbixConfigModal";
import ADConfigModal from "../../components/modals/ADConfigModal";
import M365ConfigModal from "../../components/modals/M365ConfigModal";
import HypervConfigModal from "../../components/modals/HypervConfigModal";
import ProxmoxConfigModal from "../../components/modals/ProxmoxConfigModal";
import VeeamConfigModal from "../../components/modals/VeeamConfigModal";
import UniFiConfigModal from "../../components/modals/UniFiConfigModal";

type ConfigModalType = "zabbix" | "active_directory" | "microsoft_365" | "hyperv" | "proxmox" | "veeam" | "unifi" | null;

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
    {
        type: "hyperv",
        label: "Hyper-V",
        icon: "🖥️",
        description: "Hyper-V virtualization — VMs, hosts, networks, storage and checkpoints.",
    },
    {
        type: "proxmox",
        label: "Proxmox VE",
        icon: "🐧",
        description: "Proxmox Virtual Environment — nodes, VMs, LXC containers, storage and networks.",
    },
    {
        type: "veeam",
        label: "Veeam Backup",
        icon: "💾",
        description: "Veeam B&R — backup jobs, repositories, sessions, restore points and server health.",
    },
    {
        type: "unifi",
        label: "UniFi Network",
        icon: "📶",
        description: "Ubiquiti UniFi Site Manager — sites, devices, clients, wireless and alerts.",
    },
];

export default function IntegrationsPage() {
    const [profiles, setProfiles] = useState<IntegrationProfile[]>([]);
    const [agents, setAgents] = useState<Agent[]>([]);
    const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
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
    const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set());

    const load = async () => {
        try {
            const [items, agentList] = await Promise.all([
                integrationsApi.list(),
                agentsApi.list(),
            ]);
            setProfiles(items);
            setAgents(agentList.items ?? []);
            // Auto-expand types that have profiles
            const types = new Set(items.map((p) => p.integration_type));
            setExpandedTypes((prev) => {
                const next = new Set(prev);
                types.forEach((t) => next.add(t));
                return next;
            });
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, []);

    const getProfiles = (type: string) =>
        profiles.filter((p) => p.integration_type === type);

    const toggleExpand = (type: string) => {
        setExpandedTypes((prev) => {
            const next = new Set(prev);
            if (next.has(type)) {
                next.delete(type);
            } else {
                next.add(type);
            }
            return next;
        });
    };

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

    const handleConfigure = (type: ConfigModalType, profile: IntegrationProfile | null = null) => {
        setEditingProfile(profile);
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

    if (loading) return <div className="loading-bar" />;

    return (
        <>
            <PageHeader
                title="Integrations"
                subtitle="Manage external platform connections"
                actions={
                    <select
                        className="form-input"
                        value={selectedAgentId ?? ""}
                        onChange={(e) => {
                            const val = e.target.value;
                            setSelectedAgentId(val ? Number(val) : null);
                        }}
                    >
                        <option value="">All agents / Global</option>
                        {agents.map((a) => (
                            <option key={a.id} value={a.id}>
                                #{a.id} — {a.name}
                            </option>
                        ))}
                    </select>
                }
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

            <div className="integrations-type-groups">
                {INTEGRATION_DEFS.map((def) => {
                    const typeProfiles = def.type ? getProfiles(def.type) : [];
                    const isExpanded = expandedTypes.has(def.type ?? "");
                    const connectedCount = typeProfiles.filter(
                        (p) => p.enabled && p.last_success !== null && p.last_error === null
                    ).length;
                    const hasProfiles = typeProfiles.length > 0;

                    return (
                        <div key={def.type} className={`integrations-type-group ${isExpanded ? "expanded" : ""}`}>
                            <div
                                className="integrations-type-header"
                                onClick={() => toggleExpand(def.type ?? "")}
                            >
                                <div className="integrations-type-left">
                                    <span className="integrations-type-chevron">{isExpanded ? "\u25BC" : "\u25B6"}</span>
                                    <span className="integrations-type-icon">{def.icon}</span>
                                    <span className="integrations-type-label">{def.label}</span>
                                    <span className="integrations-type-count">
                                        {typeProfiles.length > 0
                                            ? `${typeProfiles.length} connection${typeProfiles.length !== 1 ? "s" : ""}`
                                            : "Not configured"}
                                    </span>
                                </div>
                                <div className="integrations-type-right">
                                    {hasProfiles && (
                                        <span className={`integrations-type-badge ${connectedCount === typeProfiles.length ? "all-connected" : connectedCount > 0 ? "some-connected" : ""}`}>
                                            {connectedCount}/{typeProfiles.length} connected
                                        </span>
                                    )}
                                    <button
                                        className="btn btn-primary btn-sm"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleConfigure(def.type);
                                        }}
                                    >
                                        + Add
                                    </button>
                                </div>
                            </div>

                            {isExpanded && (
                                <div className="integrations-type-body">
                                    {!hasProfiles ? (
                                        <div className="integrations-type-empty">
                                            <p>{def.description}</p>
                                            <button
                                                className="btn btn-primary btn-sm"
                                                onClick={() => handleConfigure(def.type)}
                                            >
                                                Configure {def.label}
                                            </button>
                                        </div>
                                    ) : (
                                        typeProfiles.map((profile) => {
                                            const connected =
                                                profile.enabled &&
                                                profile.last_success !== null &&
                                                profile.last_error === null;
                                            return (
                                                <div
                                                    key={profile.id}
                                                    className={`integration-row ${profile.enabled ? "enabled" : ""}`}
                                                >
                                                    <div className="integration-row-main">
                                                        <div className="integration-row-info">
                                                            <strong>{profile.name}</strong>
                                                            <div className="integration-row-meta">
                                                                {profile.agent_id ? <span>Agent #{profile.agent_id}</span> : <span>Global</span>}
                                                                {profile.username && <span>{profile.username}</span>}
                                                                {profile.base_url && (
                                                                    <span className="integration-meta-url">{profile.base_url}</span>
                                                                )}
                                                                {profile.ssh_host && (
                                                                    <span>SSH: {profile.ssh_host}</span>
                                                                )}
                                                                {profile.last_test && (
                                                                    <span>Last tested: {new Date(profile.last_test).toLocaleString()}</span>
                                                                )}
                                                            </div>
                                                        </div>
                                                        <div className="integration-row-status">
                                                            {!profile.enabled ? (
                                                                <StatusBadge status="neutral" label="Disabled" />
                                                            ) : connected ? (
                                                                <StatusBadge status="healthy" label="Connected" />
                                                            ) : profile.last_error ? (
                                                                <StatusBadge status="error" label="Error" />
                                                            ) : (
                                                                <StatusBadge status="warning" label="Untested" />
                                                            )}
                                                            {testResult && testResult.id === profile.id && (
                                                                <span className={`integration-test-result ${testResult.success ? "success" : "error"}`}>
                                                                    {testResult.message}
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>
                                                    <div className="integration-row-actions">
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
                                                            onClick={() => handleConfigure(def.type, profile)}
                                                        >
                                                            Configure
                                                        </button>
                                                        <button
                                                            className="btn btn-danger btn-sm"
                                                            onClick={() => handleDelete(profile)}
                                                        >
                                                            Remove
                                                        </button>
                                                    </div>
                                                </div>
                                            );
                                        })
                                    )}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {modalType === "zabbix" && (
                <ZabbixConfigModal
                    profile={editingProfile}
                    onSave={handleModalSave}
                    onCancel={() => { setModalType(null); setEditingProfile(null); }}
                    onError={(msg) => setError(msg)}
                />
            )}
            {modalType === "active_directory" && (
                <ADConfigModal
                    profile={editingProfile}
                    onSave={handleModalSave}
                    onCancel={() => { setModalType(null); setEditingProfile(null); }}
                    onError={(msg) => setError(msg)}
                />
            )}
            {modalType === "microsoft_365" && (
                <M365ConfigModal
                    profile={editingProfile}
                    onSave={handleModalSave}
                    onCancel={() => { setModalType(null); setEditingProfile(null); }}
                    onError={(msg) => setError(msg)}
                />
            )}
            {modalType === "hyperv" && (
                <HypervConfigModal
                    profile={editingProfile}
                    onSave={handleModalSave}
                    onCancel={() => { setModalType(null); setEditingProfile(null); }}
                    onError={(msg) => setError(msg)}
                />
            )}
            {modalType === "proxmox" && (
                <ProxmoxConfigModal
                    profile={editingProfile}
                    onSave={handleModalSave}
                    onCancel={() => { setModalType(null); setEditingProfile(null); }}
                    onError={(msg) => setError(msg)}
                />
            )}
            {modalType === "veeam" && (
                <VeeamConfigModal
                    profile={editingProfile}
                    onSave={handleModalSave}
                    onCancel={() => { setModalType(null); setEditingProfile(null); }}
                    onError={(msg) => setError(msg)}
                />
            )}
            {modalType === "unifi" && (
                <UniFiConfigModal
                    profile={editingProfile}
                    onSave={handleModalSave}
                    onCancel={() => { setModalType(null); setEditingProfile(null); }}
                    onError={(msg) => setError(msg)}
                />
            )}
        </>
    );
}
