import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import { sopApi, SOPImportRequest } from "../../services/sop";

export default function SOPImportWizardPage() {
  const [sourceName, setSourceName] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceName.trim() || !title.trim()) {
      setError("Source name and title are required");
      return;
    }
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const payload: SOPImportRequest = {
        file_path: sourceName.trim(),
        source_name: sourceName.trim(),
        title: title.trim(),
        description: description || undefined,
      };
      const data = await sopApi.importDocument(payload);
      setResult(data);
    } catch (e: any) {
      setError(e.message || "Import failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageHeader title="Import SOP" subtitle="Extract operational knowledge from a temporary Word/PDF source" />
      {error && <div className="error-banner">{error}</div>}
      {result ? (
        <div className="card">
          <h3>Import Complete</h3>
          <p><strong>Document:</strong> {result.source.source_name}</p>
          <p><strong>Status:</strong> Successfully Processed</p>
          <p><strong>Content Extracted:</strong> {result.extracted_text ? "Yes" : "No"}</p>
          <p><strong>SOP Created:</strong> {result.sop.title}</p>
          <p><strong>Source Hash:</strong> {result.source.source_hash}</p>
          <p><strong>Original File:</strong> Deleted</p>
          <p><strong>Stored Permanently:</strong> No</p>
          <button className="btn" onClick={() => setResult(null)}>Import Another</button>
        </div>
      ) : (
        <form className="form-stack" onSubmit={handleSubmit}>
          <div className="form-group"><label>Source File Name *</label><input value={sourceName} onChange={(e) => setSourceName(e.target.value)} placeholder="Server_Backup_Procedure.pdf" /></div>
          <div className="form-group"><label>SOP Title *</label><input value={title} onChange={(e) => setTitle(e.target.value)} /></div>
          <div className="form-group"><label>Description</label><textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} /></div>
          <button className="btn btn-primary" type="submit" disabled={submitting}>{submitting ? "Importing…" : "Import"}</button>
        </form>
      )}
    </>
  );
}
