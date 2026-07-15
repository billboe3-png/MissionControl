import { useEffect, useState } from "react";
import { hypervApi, HyperVHost } from "../../services/hyperv";

const STORAGE_KEY = "hyperv_selected_host_id";

export function useSelectedHost(): {
    selectedHostId: number | null;
    setSelectedHostId: (id: number | null) => void;
    hosts: HyperVHost[];
    loading: boolean;
} {
    const [hosts, setHosts] = useState<HyperVHost[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedHostId, setSelectedHostIdState] = useState<number | null>(() => {
        const stored = localStorage.getItem(STORAGE_KEY);
        return stored ? parseInt(stored, 10) : null;
    });

    useEffect(() => {
        hypervApi.listHosts()
            .then((h) => {
                setHosts(h);
                if (h.length > 0 && selectedHostId === null) {
                    setSelectedHostIdState(h[0].id);
                    localStorage.setItem(STORAGE_KEY, String(h[0].id));
                }
            })
            .catch(() => {})
            .finally(() => setLoading(false));
    }, []);

    const setSelectedHostId = (id: number | null) => {
        setSelectedHostIdState(id);
        if (id !== null) {
            localStorage.setItem(STORAGE_KEY, String(id));
        } else {
            localStorage.removeItem(STORAGE_KEY);
        }
    };

    return { selectedHostId, setSelectedHostId, hosts, loading };
}

interface HyperVHostSelectorProps {
    hosts: HyperVHost[];
    selectedHostId: number | null;
    onChange: (id: number | null) => void;
}

export default function HyperVHostSelector({ hosts, selectedHostId, onChange }: HyperVHostSelectorProps) {
    if (hosts.length <= 1) return null;

    return (
        <div className="hyperv-host-selector">
            <label className="hyperv-host-selector-label">Host:</label>
            <select
                className="hyperv-host-selector-select"
                value={selectedHostId ?? ""}
                onChange={(e) => {
                    const val = e.target.value;
                    onChange(val ? parseInt(val, 10) : null);
                }}
            >
                {hosts.map((h) => (
                    <option key={h.id} value={h.id}>
                        {h.name} ({h.host})
                    </option>
                ))}
            </select>
        </div>
    );
}
