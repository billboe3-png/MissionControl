import { useEffect, useState } from "react";
import LoadingButton from "../common/LoadingButton";
import { agentsApi, AgentUpdateInput } from "../../services/agents";

const AVAILABLE_PLUGINS = [
    { value: "docker", label: "Docker" },
    { value: "linux", label: "Linux System" },
    { value: "hyperv", label: "Hyper-V" },
    { value: "windows", label: "Windows" },
    { value: "windows_docker", label: "Windows Docker" },
    { value: "zabbix", label: "Zabbix" },
    { value: "active_directory", label: "Active Directory" },
    { value: "microsoft_365", label: "Microsoft 365" },
    { value: "veeam", label: "Veeam" },
    { value: "proxmox", label: "Proxmox" },
];

interface AgentModalProps {
    agent?: {
        id: number;
        name: string;
        hostname: string;
        operating_system: string | null;
        os_version: string | null;
        ip_address: string | null;
        agent_version: string | null;
        enabled: boolean;
        health: string;
        cpu_percent: number | null;
        memory_percent: number | null;
        disk_percent: number | null;
        last_heartbeat: string | null;
        heartbeat_interval: number;
        tags: string | null;
        notes: string | null;
        active_plugins: string | null;
        enabled_plugins: string | null;
        created_at: string | null;
        updated_at: string | null;
        registered_at: string | null;
    };
    onSave: () => void;
    onCancel: () => void;
    onError: (message: string) => void;
}

export default function AgentModal({
    agent,
    onSave,
    onCancel,
    onError,
}: AgentModalProps) {
    const [name, setName] = useState(agent?.name ?? "");
    const [hostname, setHostname] = useState(agent?.hostname ?? "");
    const [operatingSystem, setOperatingSystem] = useState(
        agent?.operating_system ?? ""
    );
    const [osVersion, setOsVersion] = useState(agent?.os_version ?? "");
    const [ipAddress, setIpAddress] = useState(agent?.ip_address ?? "");
    const [agentVersion, setAgentVersion] = useState(agent?.agent_version ?? "");
    const [enabled, setEnabled] = useState(agent?.enabled ?? true);
    const [heartbeatInterval, setHeartbeatInterval] = useState(
        agent?.heartbeat_interval ?? 30
    );
    const [tags, setTags] = useState(agent?.tags ?? "");
    const [notes, setNotes] = useState(agent?.notes ?? "");
    const [selectedPlugins, setSelectedPlugins] = useState<string[]>(() => {
        const raw = agent?.enabled_plugins ?? agent?.active_plugins ?? "";
        return raw
            ? raw.split(",").map((p) => p.trim()).filter(Boolean)
            : [];
    });
    const [loading, setLoading] = useState(false);

    const isEditing = agent !== undefined;

    const togglePlugin = (value: string) => {
        setSelectedPlugins((prev) =>
            prev.includes(value)
                ? prev.filter((p) => p !== value)
                : [...prev, value]
        );
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const payload: AgentUpdateInput = {
                name,
                hostname,
                operating_system: operatingSystem || undefined,
                os_version: osVersion || undefined,
                ip_address: ipAddress || undefined,
                agent_version: agentVersion || undefined,
                enabled,
                heartbeat_interval: heartbeatInterval,
                tags: tags || undefined,
                notes: notes || undefined,
                enabled_plugins: selectedPlugins.join(",") || undefined,
            };

            if (isEditing) {
                await agentsApi.update(agent.id, payload);
            } else {
                await agentsApi.create(payload);
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
                    {isEditing ? "Edit Agent" : "Add Agent"}
                </h3>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="agent-name">Name</label>
                        <input
                            id="agent-name"
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
                            <label htmlFor="agent-hostname">Hostname</label>
                            <input
                                id="agent-hostname"
                                type="text"
                                className="form-input"
                                value={hostname}
                                onChange={(e) => setHostname(e.target.value)}
                                required
                                maxLength={500}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="agent-ip">IP Address</label>
                            <input
                                id="agent-ip"
                                type="text"
                                className="form-input"
                                value={ipAddress}
                                onChange={(e) => setIpAddress(e.target.value)}
                                maxLength={45}
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="agent-os">Operating System</label>
                        <select
                            id="agent-os"
                            className="form-input"
                            value={operatingSystem}
                            onChange={(e) => setOperatingSystem(e.target.value)}
                        >
                            <option value="">Select OS…</option>
                            <optgroup label="Windows">
                                <option value="Windows Server 2016">Windows Server 2016</option>
                                <option value="Windows Server 2019">Windows Server 2019</option>
                                <option value="Windows Server 2022">Windows Server 2022</option>
                                <option value="Windows Server 2025">Windows Server 2025</option>
                                <option value="Windows 10">Windows 10</option>
                                <option value="Windows 11">Windows 11</option>
                            </optgroup>
                            <optgroup label="Linux">
                                <option value="Ubuntu 20.04">Ubuntu 20.04</option>
                                <option value="Ubuntu 22.04">Ubuntu 22.04</option>
                                <option value="Ubuntu 24.04">Ubuntu 24.04</option>
                                <option value="Debian 11">Debian 11</option>
                                <option value="Debian 12">Debian 12</option>
                                <option value="RHEL 8">RHEL 8</option>
                                <option value="RHEL 9">RHEL 9</option>
                                <option value="Rocky Linux 8">Rocky Linux 8</option>
                                <option value="Rocky Linux 9">Rocky Linux 9</option>
                                <option value="CentOS 7">CentOS 7</option>
                                <option value="AlmaLinux 8">AlmaLinux 8</option>
                                <option value="AlmaLinux 9">AlmaLinux 9</option>
                                <option value="SUSE 15">SUSE 15</option>
                                <option value="Amazon Linux 2">Amazon Linux 2</option>
                            </optgroup>
                            <optgroup label="Other">
                                <option value="Other">Other</option>
                            </optgroup>
                        </select>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="agent-version">Agent Version</label>
                            <input
                                id="agent-version"
                                type="text"
                                className="form-input"
                                value={agentVersion}
                                onChange={(e) => setAgentVersion(e.target.value)}
                                maxLength={50}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="agent-heartbeat">Heartbeat Interval (s)</label>
                            <input
                                id="agent-heartbeat"
                                type="number"
                                className="form-input"
                                value={heartbeatInterval}
                                onChange={(e) => setHeartbeatInterval(Number(e.target.value))}
                                min={10}
                                max={300}
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label>Enabled Plugins</label>
                        <div className="plugin-multiselect">
                            {AVAILABLE_PLUGINS.map((plugin) => (
                                <label key={plugin.value} className="plugin-option">
                                    <input
                                        type="checkbox"
                                        checked={selectedPlugins.includes(plugin.value)}
                                        onChange={() => togglePlugin(plugin.value)}
                                    />
                                    <span>{plugin.label}</span>
                                </label>
                            ))}
                        </div>
                        <div style={{ opacity: 0.7, fontSize: 12, marginTop: 6 }}>
                            Selected plugins will be synced to the agent on its next heartbeat.
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="agent-tags">Tags</label>
                        <input
                            id="agent-tags"
                            type="text"
                            className="form-input"
                            value={tags}
                            onChange={(e) => setTags(e.target.value)}
                            maxLength={500}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="agent-notes">Notes</label>
                        <textarea
                            id="agent-notes"
                            className="form-input"
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            rows={3}
                        />
                    </div>

                    <div className="form-group form-group-inline">
                        <label htmlFor="agent-enabled">Enabled</label>
                        <input
                            id="agent-enabled"
                            type="checkbox"
                            checked={enabled}
                            onChange={(e) => setEnabled(e.target.checked)}
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
