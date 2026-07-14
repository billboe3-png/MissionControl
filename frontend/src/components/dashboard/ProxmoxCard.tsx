import { useNavigate } from "react-router-dom";
import { ProxmoxStatus } from "../../types/dashboard";

export default function ProxmoxCard({ data }: { data: ProxmoxStatus }) {
    const navigate = useNavigate();

    return (
        <div className="dashboard-section proxmox-card">
            <div className="proxmox-card-header">
                <h3>Proxmox VE</h3>
                <button
                    className="btn btn-link btn-sm"
                    onClick={() => navigate("/proxmox")}
                >
                    Manage
                </button>
            </div>
            {!data.connected ? (
                <p className="settings-hint">Not connected.</p>
            ) : (
                <div className="proxmox-card-stats">
                    <span>{data.nodes_online}/{data.nodes_total} nodes</span>
                    <span>{data.running} VMs running</span>
                    <span>{data.running_lxc} LXCs running</span>
                    <span>{data.total_memory_gb} GB total</span>
                </div>
            )}
        </div>
    );
}
