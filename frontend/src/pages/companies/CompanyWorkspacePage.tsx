import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import SearchInput from "../../components/common/SearchInput";
import { companiesApi, CompanyData } from "../../services/company";

export default function CompanyWorkspacePage() {
    const [companies, setCompanies] = useState<CompanyData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [search, setSearch] = useState("");
    const navigate = useNavigate();

    const loadData = useCallback(async () => {
        try {
            const data = await companiesApi.list();
            setCompanies(data);
        } catch (e: any) {
            setError(e.message || "Failed to load");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
        const id = setInterval(loadData, 30000);
        return () => clearInterval(id);
    }, [loadData]);

    const filtered = companies.filter((c) => {
        if (!search) return true;
        const q = search.toLowerCase();
        return (
            c.name.toLowerCase().includes(q) ||
            c.display_name.toLowerCase().includes(q)
        );
    });

    const totalSites = companies.reduce((s, c) => s + c.site_count, 0);
    const totalAgents = companies.reduce((s, c) => s + c.agent_count, 0);
    const totalIntegrations = companies.reduce((s, c) => s + c.integration_count, 0);

    return (
        <>
            <PageHeader
                title="Company & Site Workspace"
                subtitle="Multi-tenant infrastructure overview"
            />

            {error && <div className="error-banner">{error}</div>}

            {loading ? (
                <div className="loading-bar" />
            ) : (
                <>
                    <div className="fleet-stats-bar">
                        <div className="fleet-stat-chip">
                            <span className="fleet-stat-chip-value">{companies.length}</span>
                            <span className="fleet-stat-chip-label">Companies</span>
                        </div>
                        <div className="fleet-stat-chip">
                            <span className="fleet-stat-chip-value">{totalSites}</span>
                            <span className="fleet-stat-chip-label">Sites</span>
                        </div>
                        <div className="fleet-stat-chip success">
                            <span className="fleet-stat-chip-value">{totalAgents}</span>
                            <span className="fleet-stat-chip-label">Agents</span>
                        </div>
                        <div className="fleet-stat-chip">
                            <span className="fleet-stat-chip-value">{totalIntegrations}</span>
                            <span className="fleet-stat-chip-label">Integrations</span>
                        </div>
                    </div>

                    <div className="fleet-toolbar">
                        <SearchInput value={search} onChange={setSearch} placeholder="Search companies..." />
                    </div>

                    {filtered.length === 0 ? (
                        <div className="empty-state">
                            <span className="empty-state-icon">🏢</span>
                            <h3 className="empty-state-title">No companies</h3>
                            <p className="empty-state-description">
                                Add companies to organize your multi-tenant infrastructure.
                            </p>
                        </div>
                    ) : (
                        <div className="company-workspace-grid">
                            {filtered.map((company) => (
                                <div
                                    key={company.id}
                                    className="company-workspace-card"
                                    style={{ cursor: "pointer" }}
                                    onClick={() => navigate(`/companies/${company.id}`)}
                                >
                                    <div className="company-workspace-header">
                                        <span className="company-workspace-name">
                                            {company.display_name}
                                        </span>
                                        <StatusBadge
                                            status={company.enabled ? "healthy" : "error"}
                                            label={company.enabled ? "Active" : "Disabled"}
                                        />
                                    </div>
                                    <div style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                                        {company.license_type || "Standard"} licence
                                        {company.primary_contact && ` · ${company.primary_contact}`}
                                    </div>
                                    <div className="company-workspace-stats">
                                        <div className="company-workspace-stat">
                                            <span className="company-workspace-stat-value">
                                                {company.site_count}
                                            </span>
                                            <span className="company-workspace-stat-label">Sites</span>
                                        </div>
                                        <div className="company-workspace-stat">
                                            <span className="company-workspace-stat-value">
                                                {company.agent_count}
                                            </span>
                                            <span className="company-workspace-stat-label">Agents</span>
                                        </div>
                                        <div className="company-workspace-stat">
                                            <span className="company-workspace-stat-value">
                                                {company.integration_count}
                                            </span>
                                            <span className="company-workspace-stat-label">Integrations</span>
                                        </div>
                                    </div>
                                    {company.contact_email && (
                                        <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                                            {company.contact_email}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}
        </>
    );
}
