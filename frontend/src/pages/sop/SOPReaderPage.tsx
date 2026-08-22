import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import { sopApi, SOP, SOPVersionResponse, AIQueryResponse } from "../../services/sop";

export default function SOPReaderPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [sop, setSop] = useState<SOP | null>(null);
  const [versions, setVersions] = useState<SOPVersionResponse[]>([]);
  const [aiAnswer, setAiAnswer] = useState<AIQueryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [sopData, versionsData] = await Promise.all([
        sopApi.get(Number(id)),
        sopApi.versions(Number(id)),
      ]);
      setSop(sopData);
      setVersions(versionsData);
    } catch (e: any) {
      setError(e.message || "Failed to load SOP");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const askAi = async () => {
    if (!sop) return;
    setAiLoading(true);
    setAiAnswer(null);
    try {
      const data = await sopApi.aiQuery(`Explain this SOP: ${sop.title}`);
      setAiAnswer(data);
    } catch (e: any) {
      setError(e.message || "AI query failed");
    } finally {
      setAiLoading(false);
    }
  };

  if (loading) return <div className="loading-bar">Loading SOP…</div>;
  if (error) return <div className="error-banner">{error}</div>;
  if (!sop) return <div className="empty-state">SOP not found.</div>;

  return (
    <>
      <PageHeader title={sop.title} subtitle={`SOP #${sop.id} • ${sop.status}`} actions={<button className="btn" onClick={() => navigate(`/sop/${sop.id}/edit`)}>Edit</button>} />
      <div className="card">
        <h3>Details</h3>
        <p><strong>Status:</strong> {sop.status}</p>
        <p><strong>Version:</strong> {sop.current_version || "—"}</p>
        <p><strong>Updated:</strong> {new Date(sop.updated_at).toLocaleString()}</p>
        {sop.description && <p><strong>Description:</strong> {sop.description}</p>}
        {sop.purpose && <p><strong>Purpose:</strong> {sop.purpose}</p>}
        {sop.scope && <p><strong>Scope:</strong> {sop.scope}</p>}
        {sop.procedure && (
          <div>
            <h4>Procedure</h4>
            <pre className="prose whitespace-pre-wrap">{sop.procedure}</pre>
          </div>
        )}
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <h3>AI Assistant</h3>
        <button className="btn btn-primary" onClick={askAi} disabled={aiLoading}>{aiLoading ? "Thinking…" : "Ask Dexter about this SOP"}</button>
        {aiAnswer && (
          <div style={{ marginTop: 12 }}>
            <p><strong>Answer:</strong> {aiAnswer.answer}</p>
            <p><strong>Confidence:</strong> {Math.round((aiAnswer.confidence.score || 0) * 100)}%</p>
          </div>
        )}
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <h3>Versions</h3>
        {versions.length === 0 && <div className="empty-state">No versions yet.</div>}
        <table className="data-table">
          <thead><tr><th>Version</th><th>Created</th><th>Created By</th><th>Change Reason</th></tr></thead>
          <tbody>
            {versions.map((version) => (
              <tr key={version.id}>
                <td>{version.version}</td>
                <td>{new Date(version.created_at).toLocaleString()}</td>
                <td>{version.created_by || "—"}</td>
                <td>{version.change_reason || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
