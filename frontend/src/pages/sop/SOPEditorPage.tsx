import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import { sopApi, SOP, SOPUpdateInput } from "../../services/sop";

export default function SOPEditorPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [sop, setSop] = useState<SOP | null>(null);
  const [form, setForm] = useState<SOPUpdateInput>({ title: "", description: "", purpose: "", procedure: "", scope: "", audience: "", responsibilities: "", prerequisites: "", validation: "", troubleshooting: "", escalation: "", rollback: "", references: "" });
  const [saving, setSaving] = useState(false);
  const [changeReason, setChangeReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const data = await sopApi.get(Number(id));
      setSop(data);
      setForm({
        title: data.title,
        description: data.description || "",
        purpose: data.purpose || "",
        procedure: data.procedure || "",
        validation: data.validation || "",
        troubleshooting: data.troubleshooting || "",
        escalation: data.escalation || "",
        rollback: data.rollback || "",
        references: data.references || "",
      });
    } catch (e: any) {
      setError(e.message || "Failed to load SOP");
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const handleSave = async () => {
    if (!id) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await sopApi.update(Number(id), form, changeReason);
      setSop(updated);
      setMessage("Saved. A new version was created if a change reason was provided.");
      setChangeReason("");
    } catch (e: any) {
      setError(e.message || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async () => {
    if (!id) return;
    try { await sopApi.submit(Number(id)); setMessage("Submitted for approval."); } catch (e: any) { setError(e.message); }
  };

  const handlePublish = async () => {
    if (!id) return;
    try { await sopApi.publish(Number(id)); setMessage("Published."); } catch (e: any) { setError(e.message); }
  };

  if (!sop) return <div className="loading-bar">Loading SOP…</div>;

  return (
    <>
      <PageHeader title={`Edit: ${sop.title}`} subtitle={`SOP #${sop.id}`} actions={<><button className="btn" onClick={handleSubmit}>Submit</button><button className="btn" onClick={handlePublish}>Publish</button></>} />
      {error && <div className="error-banner">{error}</div>}
      {message && <div className="success-banner">{message}</div>}
      <div className="form-stack">
        <div className="form-group"><label>Title</label><textarea rows={2} value={form.title || ""} onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
        <div className="form-group"><label>Purpose</label><textarea rows={3} value={form.purpose || ""} onChange={(e) => setForm({ ...form, purpose: e.target.value })} /></div>
        <div className="form-group"><label>Procedure</label><textarea rows={8} value={form.procedure || ""} onChange={(e) => setForm({ ...form, procedure: e.target.value })} /></div>
        <div className="form-group"><label>Validation</label><textarea rows={3} value={form.validation || ""} onChange={(e) => setForm({ ...form, validation: e.target.value })} /></div>
        <div className="form-group"><label>Troubleshooting</label><textarea rows={3} value={form.troubleshooting || ""} onChange={(e) => setForm({ ...form, troubleshooting: e.target.value })} /></div>
        <div className="form-group"><label>Escalation</label><textarea rows={3} value={form.escalation || ""} onChange={(e) => setForm({ ...form, escalation: e.target.value })} /></div>
        <div className="form-group"><label>Rollback</label><textarea rows={3} value={form.rollback || ""} onChange={(e) => setForm({ ...form, rollback: e.target.value })} /></div>
        <div className="form-group"><label>References</label><textarea rows={3} value={form.references || ""} onChange={(e) => setForm({ ...form, references: e.target.value })} /></div>
        <div className="form-group"><label>Change Reason</label><input value={changeReason} onChange={(e) => setChangeReason(e.target.value)} placeholder="Optional version reason" /></div>
        <div className="form-actions"><button className="btn btn-primary" onClick={handleSave} disabled={saving}>{saving ? "Saving..." : "Save"}</button></div>
      </div>
    </>
  );
}
