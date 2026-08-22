import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { sopApi, SOPDocument, SOPDocumentCreateInput } from "../../services/sop";

type StatusFilter = "all" | "draft" | "active" | "archived";
type ApprovalFilter = "all" | "pending" | "approved" | "rejected";

export default function SOPDocumentsPage() {
  const [documents, setDocuments] = useState<SOPDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [approvalFilter, setApprovalFilter] = useState<ApprovalFilter>("all");

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await sopApi.list();
      let items = data.items;
      if (statusFilter !== "all") {
        items = items.filter((item) => item.status === statusFilter);
      }
      if (approvalFilter !== "all") {
        items = items.filter((item) => item.approval_status === approvalFilter);
      }
      setDocuments(items);
    } catch (e: any) {
      setError(e.message || "Failed to load SOP documents");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, approvalFilter]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  return (
    <>
      <PageHeader
        title="Standard Operating Procedures"
        subtitle="Upload PDF/Word SOPs, track approval status, and view extracted text"
        actions={
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            + New SOP
          </button>
        }
      />

      {error && <div className="error-banner">{error}</div>}

      <div className="toolbar">
        <div className="filters">
          <label>Status:</label>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}>
            <option value="all">All</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </select>
          <label>Approval:</label>
          <select
            value={approvalFilter}
            onChange={(e) => setApprovalFilter(e.target.value as ApprovalFilter)}
          >
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loading-bar">Loading SOP documents…</div>
      ) : documents.length === 0 ? (
        <div className="empty-state">
          <h3>No SOPs</h3>
          <p>Upload a PDF or Word SOP to get started.</p>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            + New SOP
          </button>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Approval</th>
                <th>Version</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td>
                    <strong>{doc.title}</strong>
                    {doc.description && (
                      <div style={{ fontSize: "0.85em", opacity: 0.6 }}>{doc.description}</div>
                    )}
                  </td>
                  <td>
                    <span className={`status-badge ${doc.status === "active" ? "status-ok" : "status-disabled"}`}>
                      {doc.status}
                    </span>
                  </td>
                  <td>
                    <span
                      className={`status-badge ${doc.approval_status === "approved" ? "status-ok" : doc.approval_status === "rejected" ? "status-critical" : "status-warning"}`}
                    >
                      {doc.approval_status}
                    </span>
                  </td>
                  <td>{doc.version || "—"}</td>
                  <td>{new Date(doc.updated_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreate && (
        <SOPCreateModal onClose={() => setShowCreate(false)} onSaved={loadDocuments} />
      )}
    </>
  );
}

function SOPCreateModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [version, setVersion] = useState("");
  const [createdBy, setCreatedBy] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError("Title is required");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload: SOPDocumentCreateInput = {
        title: title.trim(),
        description: description || undefined,
        version: version || undefined,
        created_by: createdBy || undefined,
        status: "draft",
        approval_status: "pending",
      };
      await sopApi.create(payload);
      onSaved();
      onClose();
    } catch (e: any) {
      setError(e.message || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>New SOP</h2>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body">
          {error && <div className="alert alert-error">{error}</div>}

          <div className="form-group">
            <label>Title *</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Firewall change control SOP" />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
          </div>

          <div className="form-group">
            <label>Version</label>
            <input value={version} onChange={(e) => setVersion(e.target.value)} placeholder="e.g. 1.0" />
          </div>

          <div className="form-group">
            <label>Created By</label>
            <input value={createdBy} onChange={(e) => setCreatedBy(e.target.value)} placeholder="e.g. Robert Barnes" />
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn" onClick={onClose} disabled={saving}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={saving}>
            {saving ? "Saving..." : "Create"}
          </button>
        </div>
      </div>
    </div>
  );
}
