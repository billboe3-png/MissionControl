import { useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import { api } from "../../services/api";

export default function ProfilePage() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (next !== confirm) {
      setError("New password and confirmation do not match");
      return;
    }
    setLoading(true);
    try {
      await api.changePassword(current, next);
      setSuccess("Password updated");
      setCurrent("");
      setNext("");
      setConfirm("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to change password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-4">
      <PageHeader title="Profile" subtitle="Update your account password" />
      <form onSubmit={submit} className="max-w-lg space-y-3">
        {error && <div className="error-banner">{error}</div>}
        {success && <div className="success-banner">{success}</div>}
        <div>
          <label className="block text-sm text-gray-400 mb-1">Current password</label>
          <input className="w-full bg-gray-800 border border-gray-700 text-gray-200 rounded px-3 py-2" type="password" value={current} onChange={(e) => setCurrent(e.target.value)} required />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">New password</label>
          <input className="w-full bg-gray-800 border border-gray-700 text-gray-200 rounded px-3 py-2" type="password" value={next} onChange={(e) => setNext(e.target.value)} required />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Confirm new password</label>
          <input className="w-full bg-gray-800 border border-gray-700 text-gray-200 rounded px-3 py-2" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
        </div>
        <button disabled={loading} className="bg-cyan-600 hover:bg-cyan-700 disabled:opacity-60 text-gray-100 rounded px-4 py-2">
          {loading ? "Updating..." : "Change password"}
        </button>
      </form>
    </div>
  );
}
