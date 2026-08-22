import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import { sopApi, SOP, SOPCreateInput, SOPImportRequest, SOPVersionResponse } from "../../services/sop";

type StatusFilter = "all" | "draft" | "pending_review" | "pending_approval" | "approved" | "published" | "rejected" | "archived";

export default function SOPLibraryPage() {
  const [items, setItems] = useState<SOP[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [query, setQuery] = useState("");
  const [selectedSOP, setSelectedSOP] = useState<SOP | null>(null);
  const [versions, setVersions] = useState<SOPVersionResponse[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await sopApi.list({ status: statusFilter === "all" ? undefined : statusFilter, q: query || undefined });
      setItems(data.items);
    } catch (e: any) {
      setError(e.message || "Failed to load SOPs");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, query]);

  useEffect(() => {
    load();
  }, [load]);

  const openSOP = async (sop: SOP) => {
    setSelectedSOP(sop);
    try {
      const data = await sopApi.versions(sop.id);
      setVersions(data);
    } catch {
      setVersions([]);
    }
  };

  return (
    <>
      <PageHeader
        title="SOP Library"
        subtitle="Published operational knowledge"
        actions={
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            + New SOP
          </button>
        }
      />

      {error && <div className="error-banner">{error}</div>}

      <div className="toolbar">
        <input
          placeholder="Search SOPs..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
        />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}>
          <option value="all">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="pending_review">Pending Review</option>
          <option value="pending_approval">Pending Approval</option>
          <option value="approved">Approved</option>
          <option value="published">Published</option>
          <option value="rejected">Rejected</option>
          <option value="archived">Archived</option>
        </select>
        <button className="btn" onClick={load}>Refresh</button>
      </div>

      {loading ? (
        <div className="loading-bar">Loading SOPs…</div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <h3>No SOPs</h3>
          <p>Create or import an SOP to get started.</p>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>+ New SOP</button>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Version</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} onClick={() => openSOP(item)} style={{ cursor: "pointer" }}>
                  <td>
                    <strong>{item.title}</strong>
                    {item.description && <div style={{ fontSize: "0.85em", opacity: 0.6 }}>{item.description}</div>}
                  </td>
                  <td><span className={`status-badge ${item.status === "published" ? "status-ok" : item.status === "approved" ? "status-ok" : "status-warning"}`}>{item.status}</span></td>
                  <td>{item.current_version || "—"}</td>
                  <td>{new Date(item.updated_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreate && <SOPCreateModal onClose={() => setShowCreate(false)} onSaved={load} />}

      {selectedSOP && (
        <div className="modal-overlay" onClick={() => setSelectedSOP(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ width: "720px" }}>
            <div className="modal-header">
              <h2>{selectedSOP.title}</h2>
              <button className="modal-close" onClick={() => setSelectedSOP(null)}>&times;</button>
            </div>
            <div className="modal-body">
              <p><strong>Status:</strong> {selectedSOP.status}</p>
              {selectedSOP.purpose && <p><strong>Purpose:</strong> {selectedSOP.purpose}</p>}
              {selectedSOP.procedure && <div style={{ marginTop: "0.5rem" }}><strong>Procedure</strong><pre style={{ whiteSpace: "pre-wrap" }}>{selectedSOP.procedure}</pre></div>}
              <h3 style={{ marginTop: "1rem" }}>Versions</h3>
              {versions.length === 0 ? <p>No versions.</p> : (
                <ul>
                  {versions.map((v) => (
                    <li key={v.id}>{v.version} — {v.status} — {new Date(v.created_at).toLocaleString()}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function SOPCreateModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [purpose, setPurpose] = useState("");
  const [procedure, setProcedure] = useState("");
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
      await sopApi.create({
        title: title.trim(),
        description: description || undefined,
        purpose: purpose || undefined,
        procedure: procedure || undefined,
      });
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
            <input value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
          </div>
          <div className="form-group">
            <label>Purpose</label>
            <textarea value={purpose} onChange={(e) => setPurpose(e.target.value)} rows={3} />
          </div>
          <div className="form-group">
            <label>Procedure</label>
            <textarea value={procedure} onChange={(e) => setProcedure(e.target.value)} rows={5} />
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn" onClick={onClose} disabled={saving}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={saving}>{saving ? "Saving..." : "Create"}</button>
        </div>
      </div>
    </div>
  );
}
