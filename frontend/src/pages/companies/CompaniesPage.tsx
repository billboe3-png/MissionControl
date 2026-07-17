import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import { useToast } from "../../contexts/ToastContext";
import { companiesApi, CompanyData } from "../../services/company";
import CompanyModal from "./CompanyModal";

export default function CompaniesPage() {
    const [companies, setCompanies] = useState<CompanyData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [editingCompany, setEditingCompany] = useState<CompanyData | undefined>(undefined);
    const { showToast } = useToast();
    const navigate = useNavigate();

    const loadData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await companiesApi.list();
            setCompanies(data);
        } catch (e: any) {
            setError(e.message || "Failed to load companies");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleDelete = async (company: CompanyData) => {
        if (!window.confirm(`Delete company "${company.display_name}"?`)) return;
        try {
            await companiesApi.remove(company.id);
            showToast("Company deleted", "success");
            loadData();
        } catch (e: any) {
            showToast(e.message || "Delete failed", "error");
        }
    };

    const handleSave = () => {
        setShowModal(false);
        setEditingCompany(undefined);
        loadData();
        showToast(editingCompany ? "Company updated" : "Company created", "success");
    };

    return (
        <>
            <PageHeader
                title="Companies"
                subtitle="Manage tenants and organizational units"
                actions={
                    <button
                        className="btn btn-primary"
                        onClick={() => { setEditingCompany(undefined); setShowModal(true); }}
                    >
                        + Add Company
                    </button>
                }
            />

            {error && <div className="error-banner">{error}</div>}

            {loading ? (
                <div className="loading-bar" />
            ) : companies.length === 0 ? (
                <div className="empty-state">
                    <h3>No Companies</h3>
                    <p>Add your first company to get started with multi-tenant management.</p>
                    <button className="btn btn-primary" onClick={() => { setEditingCompany(undefined); setShowModal(true); }}>
                        + Add Company
                    </button>
                </div>
            ) : (
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Status</th>
                                <th>Licence</th>
                                <th>Sites</th>
                                <th>Agents</th>
                                <th>Integrations</th>
                                <th>Contact</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {companies.map((c) => (
                                <tr
                                    key={c.id}
                                    style={{ cursor: "pointer" }}
                                    onClick={() => navigate(`/companies/${c.id}`)}
                                >
                                    <td>
                                        <strong>{c.display_name}</strong>
                                        <div style={{ fontSize: "0.85em", opacity: 0.6 }}>{c.name}</div>
                                    </td>
                                    <td>
                                        <span className={`status-badge ${c.enabled ? "status-ok" : "status-disabled"}`}>
                                            {c.enabled ? "Active" : "Disabled"}
                                        </span>
                                    </td>
                                    <td>{c.license_type || "—"}</td>
                                    <td>{c.site_count}</td>
                                    <td>{c.agent_count}</td>
                                    <td>{c.integration_count}</td>
                                    <td>{c.primary_contact || c.contact_email || "—"}</td>
                                    <td onClick={(e) => e.stopPropagation()}>
                                        <button
                                            className="btn btn-sm"
                                            onClick={() => { setEditingCompany(c); setShowModal(true); }}
                                        >
                                            Edit
                                        </button>
                                        <button
                                            className="btn btn-sm btn-danger"
                                            onClick={() => handleDelete(c)}
                                        >
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {showModal && (
                <CompanyModal
                    company={editingCompany}
                    onSave={handleSave}
                    onCancel={() => { setShowModal(false); setEditingCompany(undefined); }}
                />
            )}
        </>
    );
}
