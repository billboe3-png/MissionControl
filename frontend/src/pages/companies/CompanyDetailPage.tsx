import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import { useToast } from "../../contexts/ToastContext";
import { companiesApi, CompanyData } from "../../services/company";
import CompanyModal from "./CompanyModal";

export default function CompanyDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { showToast } = useToast();
    const [company, setCompany] = useState<CompanyData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showEditModal, setShowEditModal] = useState(false);

    const loadData = useCallback(async () => {
        if (!id) return;
        setLoading(true);
        setError(null);
        try {
            const data = await companiesApi.get(parseInt(id, 10));
            setCompany(data);
        } catch (e: any) {
            setError(e.message || "Failed to load company");
        } finally {
            setLoading(false);
        }
    }, [id]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleDelete = async () => {
        if (!company) return;
        if (!window.confirm(`Delete company "${company.display_name}"?`)) return;
        try {
            await companiesApi.remove(company.id);
            showToast("Company deleted", "success");
            navigate("/companies");
        } catch (e: any) {
            showToast(e.message || "Delete failed", "error");
        }
    };

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;
    if (!company) return null;

    return (
        <>
            <PageHeader
                title={company.display_name}
                subtitle={company.name}
                actions={
                    <>
                        <button className="btn" onClick={() => navigate("/companies")}>
                            ← Back
                        </button>
                        <button className="btn btn-primary" onClick={() => setShowEditModal(true)}>
                            Edit
                        </button>
                        <button className="btn btn-danger" onClick={handleDelete}>
                            Delete
                        </button>
                    </>
                }
            />

            <div className="detail-grid">
                <div className="detail-card">
                    <h3>General</h3>
                    <div className="detail-row"><span className="label">Name</span><span>{company.display_name}</span></div>
                    <div className="detail-row"><span className="label">Slug</span><span>{company.name}</span></div>
                    <div className="detail-row"><span className="label">Status</span>
                        <span className={`status-badge ${company.enabled ? "status-ok" : "status-disabled"}`}>
                            {company.enabled ? "Active" : "Disabled"}
                        </span>
                    </div>
                    <div className="detail-row"><span className="label">Licence</span><span>{company.license_type || "—"}</span></div>
                    <div className="detail-row"><span className="label">Timezone</span><span>{company.timezone || "—"}</span></div>
                    <div className="detail-row"><span className="label">Global</span><span>{company.is_global ? "Yes" : "No"}</span></div>
                </div>

                <div className="detail-card">
                    <h3>Contact</h3>
                    <div className="detail-row"><span className="label">Primary Contact</span><span>{company.primary_contact || "—"}</span></div>
                    <div className="detail-row"><span className="label">Email</span><span>{company.contact_email || "—"}</span></div>
                    <div className="detail-row"><span className="label">Phone</span><span>{company.contact_phone || "—"}</span></div>
                </div>

                <div className="detail-card">
                    <h3>Limits</h3>
                    <div className="detail-row"><span className="label">Max Sites</span><span>{company.max_sites}</span></div>
                    <div className="detail-row"><span className="label">Max Agents</span><span>{company.max_agents}</span></div>
                    <div className="detail-row"><span className="label">Max Users</span><span>{company.max_users}</span></div>
                </div>

                <div className="detail-card">
                    <h3>Resources</h3>
                    <div className="detail-row"><span className="label">Sites</span><span>{company.site_count}</span></div>
                    <div className="detail-row"><span className="label">Agents</span><span>{company.agent_count}</span></div>
                    <div className="detail-row"><span className="label">Integrations</span><span>{company.integration_count}</span></div>
                </div>
            </div>

            {company.notes && (
                <div className="detail-card" style={{ marginTop: "1rem" }}>
                    <h3>Notes</h3>
                    <p>{company.notes}</p>
                </div>
            )}

            {showEditModal && (
                <CompanyModal
                    company={company}
                    onSave={() => { setShowEditModal(false); loadData(); showToast("Company updated", "success"); }}
                    onCancel={() => setShowEditModal(false)}
                />
            )}
        </>
    );
}
