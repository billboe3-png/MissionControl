import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import SearchInput from "../../components/common/SearchInput";
import EmptyState from "../../components/common/EmptyState";
import { useToast } from "../../contexts/ToastContext";
import {
    automationApi,
    PlaybookData,
} from "../../services/automation";

const CATEGORY_META: Record<string, { icon: string; label: string }> = {
    deployment: { icon: "🚀", label: "Deployment" },
    monitoring: { icon: "📊", label: "Monitoring" },
    maintenance: { icon: "🔧", label: "Maintenance" },
    security: { icon: "🔒", label: "Security" },
    backup: { icon: "💾", label: "Backup & Recovery" },
    network: { icon: "🌐", label: "Network" },
    docker: { icon: "🐳", label: "Docker" },
    testing: { icon: "🧪", label: "Testing" },
    windows: { icon: "🪟", label: "Windows" },
    linux: { icon: "🐧", label: "Linux" },
    hyperv: { icon: "☁️", label: "Hyper-V" },
    proxmox: { icon: "🖥️", label: "Proxmox" },
    m365: { icon: "📧", label: "Microsoft 365" },
    ad: { icon: "🏢", label: "Active Directory" },
    remote: { icon: "📡", label: "Remote" },
    zabbix: { icon: "📈", label: "Zabbix" },
    general: { icon: "📋", label: "General" },
};

const DEFAULT_META = { icon: "📋", label: "Other" };

export default function PlaybooksPage() {
    const [items, setItems] = useState<PlaybookData[]>([]);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { showToast } = useToast();
    const navigate = useNavigate();

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await automationApi.listPlaybooks(search || undefined);
            setItems(data.items);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to load playbooks");
        } finally {
            setLoading(false);
        }
    }, [search]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        try {
            const text = await file.text();
            const data = JSON.parse(text);
            if (!data.playbook) {
                showToast("Invalid playbook file", "error");
                return;
            }
            await automationApi.importPlaybook(data);
            showToast("Playbook imported", "success");
            loadData();
        } catch (err: unknown) {
            showToast(err instanceof Error ? err.message : "Import failed", "error");
        } finally {
            e.target.value = "";
        }
    };

    const grouped = useMemo(() => {
        const map = new Map<string, PlaybookData[]>();
        for (const pb of items) {
            const key = (pb.category ?? "general").toLowerCase();
            if (!map.has(key)) map.set(key, []);
            map.get(key)!.push(pb);
        }
        const order = [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]));
        return order;
    }, [items]);

    return (
        <>
            <PageHeader
                title="Playbooks"
                subtitle="Define and manage automation playbooks"
                actions={
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                        <label className="btn btn-secondary" style={{ cursor: "pointer" }}>
                            Import
                            <input
                                type="file"
                                accept=".json"
                                style={{ display: "none" }}
                                onChange={handleImport}
                            />
                        </label>
                        <button
                            className="btn btn-primary"
                            onClick={() => navigate("/automation/playbooks/new")}
                        >
                            + New Playbook
                        </button>
                    </div>
                }
            />
            <SearchInput
                value={search}
                onChange={setSearch}
                placeholder="Search playbooks…"
            />
            {error && <div className="error-banner">{error}</div>}
            {loading ? (
                <div className="loading-bar" />
            ) : items.length === 0 ? (
                <EmptyState
                    icon="📋"
                    title="No playbooks"
                    description="Create your first playbook to automate operations."
                />
            ) : (
                grouped.map(([cat, playbooks]) => {
                    const meta = CATEGORY_META[cat] ?? DEFAULT_META;
                    return (
                        <div key={cat} className="identity-overview-section">
                            <h3>{meta.icon} {meta.label} ({playbooks.length})</h3>
                            <div className="quick-commands-grid">
                                {playbooks.map((pb) => (
                                    <button
                                        key={pb.id}
                                        className="quick-command-card"
                                        onClick={() => navigate(`/automation/playbooks/${pb.id}`)}
                                    >
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", width: "100%" }}>
                                            <span className="quick-command-icon">{meta.icon}</span>
                                            <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                                                {pb.requires_approval && (
                                                    <span className="badge badge-warning" style={{ fontSize: "0.65rem", padding: "2px 6px" }}>Approval</span>
                                                )}
                                                <span
                                                    className={`status-badge ${pb.enabled ? "green" : "gray"}`}
                                                    style={{ fontSize: "0.7rem" }}
                                                >
                                                    <span className="status-badge-dot" />
                                                    {pb.enabled ? "Active" : "Disabled"}
                                                </span>
                                            </div>
                                        </div>
                                        <span className="quick-command-label">{pb.name}</span>
                                        <span className="quick-command-desc">
                                            {pb.description ?? "No description"}
                                        </span>
                                        <div style={{ display: "flex", gap: "8px", alignItems: "center", marginTop: "4px", width: "100%" }}>
                                            <code className="quick-command-code">v{pb.version}</code>
                                            {pb.auto_rollback && (
                                                <code className="quick-command-code">auto-rollback</code>
                                            )}
                                            <span style={{ marginLeft: "auto", fontSize: "0.7rem", color: "var(--text-muted)" }}>
                                                {new Date(pb.updated_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    );
                })
            )}
        </>
    );
}
