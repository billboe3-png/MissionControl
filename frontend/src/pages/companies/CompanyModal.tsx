import { useState } from "react";
import { companiesApi, CompanyData, CompanyCreateInput, CompanyUpdateInput } from "../../services/company";

interface Props {
    company?: CompanyData;
    onSave: () => void;
    onCancel: () => void;
}

export default function CompanyModal({ company, onSave, onCancel }: Props) {
    const [name, setName] = useState(company?.name ?? "");
    const [displayName, setDisplayName] = useState(company?.display_name ?? "");
    const [status, setStatus] = useState(company?.status ?? "active");
    const [licenseType, setLicenseType] = useState(company?.license_type ?? "");
    const [primaryContact, setPrimaryContact] = useState(company?.primary_contact ?? "");
    const [contactEmail, setContactEmail] = useState(company?.contact_email ?? "");
    const [contactPhone, setContactPhone] = useState(company?.contact_phone ?? "");
    const [timezone, setTimezone] = useState(company?.timezone ?? "");
    const [notes, setNotes] = useState(company?.notes ?? "");
    const [maxSites, setMaxSites] = useState(String(company?.max_sites ?? 10));
    const [maxAgents, setMaxAgents] = useState(String(company?.max_agents ?? 100));
    const [maxUsers, setMaxUsers] = useState(String(company?.max_users ?? 50));
    const [error, setError] = useState<string | null>(null);
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
        if (!name.trim()) { setError("Name is required"); return; }
        if (!displayName.trim()) { setError("Display name is required"); return; }

        setSaving(true);
        setError(null);
        try {
            if (company) {
                const updateData: CompanyUpdateInput = {
                    name: name.trim(),
                    display_name: displayName.trim(),
                    status,
                    license_type: licenseType || undefined,
                    primary_contact: primaryContact || undefined,
                    contact_email: contactEmail || undefined,
                    contact_phone: contactPhone || undefined,
                    timezone: timezone || undefined,
                    notes: notes || undefined,
                    max_sites: parseInt(maxSites, 10) || 10,
                    max_agents: parseInt(maxAgents, 10) || 100,
                    max_users: parseInt(maxUsers, 10) || 50,
                };
                await companiesApi.update(company.id, updateData);
            } else {
                const createData: CompanyCreateInput = {
                    name: name.trim(),
                    display_name: displayName.trim(),
                    status,
                    license_type: licenseType || undefined,
                    primary_contact: primaryContact || undefined,
                    contact_email: contactEmail || undefined,
                    contact_phone: contactPhone || undefined,
                    timezone: timezone || undefined,
                    notes: notes || undefined,
                    max_sites: parseInt(maxSites, 10) || 10,
                    max_agents: parseInt(maxAgents, 10) || 100,
                    max_users: parseInt(maxUsers, 10) || 50,
                };
                await companiesApi.create(createData);
            }
            onSave();
        } catch (e: any) {
            setError(e.message || "Save failed");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>{company ? "Edit Company" : "New Company"}</h2>
                    <button className="modal-close" onClick={onCancel}>&times;</button>
                </div>
                <div className="modal-body">
                    {error && <div className="alert alert-error">{error}</div>}

                    <div className="form-row">
                        <div className="form-group">
                            <label>Name *</label>
                            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. acme-corp" />
                        </div>
                        <div className="form-group">
                            <label>Display Name *</label>
                            <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="e.g. Acme Corporation" />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label>Status</label>
                            <select value={status} onChange={(e) => setStatus(e.target.value)}>
                                <option value="active">Active</option>
                                <option value="suspended">Suspended</option>
                                <option value="trial">Trial</option>
                                <option value="churned">Churned</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label>Licence Type</label>
                            <input value={licenseType} onChange={(e) => setLicenseType(e.target.value)} placeholder="e.g. enterprise" />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label>Primary Contact</label>
                            <input value={primaryContact} onChange={(e) => setPrimaryContact(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>Contact Email</label>
                            <input type="email" value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>Contact Phone</label>
                            <input value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label>Timezone</label>
                            <input value={timezone} onChange={(e) => setTimezone(e.target.value)} placeholder="e.g. Africa/Johannesburg" />
                        </div>
                        <div className="form-group">
                            <label>Max Sites</label>
                            <input type="number" value={maxSites} onChange={(e) => setMaxSites(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>Max Agents</label>
                            <input type="number" value={maxAgents} onChange={(e) => setMaxAgents(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>Max Users</label>
                            <input type="number" value={maxUsers} onChange={(e) => setMaxUsers(e.target.value)} />
                        </div>
                    </div>

                    <div className="form-group">
                        <label>Notes</label>
                        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} />
                    </div>
                </div>
                <div className="modal-footer">
                    <button className="btn" onClick={onCancel} disabled={saving}>Cancel</button>
                    <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                        {saving ? "Saving..." : company ? "Update" : "Create"}
                    </button>
                </div>
            </div>
        </div>
    );
}
