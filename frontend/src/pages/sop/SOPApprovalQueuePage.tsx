import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import { sopApi, SOP } from "../../services/sop";

export default function SOPApprovalQueuePage() {
  const [items, setItems] = useState<SOP[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await sopApi.list({ status: "pending_approval" });
      setItems(data.items);
    } catch (e: any) {
      setError(e.message || "Failed to load approval queue");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const approve = async (id: number) => {
    await sopApi.approve(id, "Approved from queue");
    await load();
  };

  const reject = async (id: number) => {
    await sopApi.reject(id, "Rejected from queue");
    await load();
  };

  return (
    <>
      <PageHeader title="SOP Approval Queue" subtitle="SOPs awaiting approval" actions={<button className="btn" onClick={load}>Refresh</button>} />
      {error && <div className="error-banner">{error}</div>}
      {loading ? <div className="loading-bar">Loading…</div> : (
        <div className="table-container">
          <table className="data-table">
            <thead><tr><th>Title</th><th>Version</th><th>Updated</th><th>Actions</th></tr></thead>
            <tbody>
              {items.length === 0 && <tr><td colSpan={4} className="empty-state">No pending approvals.</td></tr>}
              {items.map((item) => (
                <tr key={item.id}>
                  <td><strong>{item.title}</strong></td>
                  <td>{item.current_version || "—"}</td>
                  <td>{new Date(item.updated_at).toLocaleString()}</td>
                  <td>
                    <button className="btn btn-primary" onClick={() => approve(item.id)}>Approve</button>
                    <button className="btn btn-danger" onClick={() => reject(item.id)}>Reject</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
