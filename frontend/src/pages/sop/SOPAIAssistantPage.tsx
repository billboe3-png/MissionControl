import { useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import { sopApi, AIQueryResponse } from "../../services/sop";

export default function SOPAIAssistantPage() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState<AIQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ask = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const data = await sopApi.aiQuery(query.trim());
      setAnswer(data);
    } catch (e: any) {
      setError(e.message || "AI query failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PageHeader title="AI SOP Assistant" subtitle="Ask questions against approved operational knowledge" />
      {error && <div className="error-banner">{error}</div>}
      <div className="form-stack">
        <div className="form-group">
          <label>Question</label>
          <input value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && ask()} placeholder="How do I recover a failed Veeam backup?" />
        </div>
        <button className="btn btn-primary" onClick={ask} disabled={loading}>{loading ? "Asking…" : "Ask Dexter"}</button>
      </div>
      {answer && (
        <div className="card">
          <h3>Answer</h3>
          <p>{answer.answer}</p>
          <p><strong>Sources:</strong> {answer.sources.join(", ") || "None"}</p>
          <p><strong>Confidence:</strong> {Math.round((answer.confidence.score || 0) * 100)}%</p>
        </div>
      )}
    </>
  );
}
