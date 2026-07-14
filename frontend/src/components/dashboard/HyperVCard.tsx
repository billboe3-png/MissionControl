import { useNavigate } from "react-router-dom";
import { HyperVStatus } from "../../types/dashboard";

export default function HyperVCard({ data }: { data: HyperVStatus }) {
    const navigate = useNavigate();

    return (
        <div className="dashboard-section hyperv-card">
            <div className="hyperv-card-header">
                <h3>Hyper-V</h3>
                <button
                    className="btn btn-link btn-sm"
                    onClick={() => navigate("/hyperv")}
                >
                    Manage
                </button>
            </div>
            {!data.connected ? (
                <p className="settings-hint">Not connected.</p>
            ) : (
                <div className="hyperv-card-stats">
                    <span>{data.running} running</span>
                    <span>{data.stopped} stopped</span>
                    <span>{data.total_memory_gb} GB total</span>
                </div>
            )}
        </div>
    );
}
