import { useState, useEffect } from "react";
import { agentsApi } from "../../services/agents";

interface AgentOption {
    id: number;
    name: string;
}

interface AgentSelectorProps {
    value: number | null;
    onChange: (agentId: number | null) => void;
    label?: string;
}

export default function AgentSelector({
    value,
    onChange,
    label = "Connect from agent",
}: AgentSelectorProps) {
    const [agents, setAgents] = useState<AgentOption[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        agentsApi
            .list()
            .then((res) => {
                if (!cancelled) {
                    setAgents(res.items ?? []);
                }
            })
            .catch(() => {
                if (!cancelled) {
                    setAgents([]);
                }
            })
            .finally(() => {
                if (!cancelled) {
                    setLoading(false);
                }
            });
        return () => {
            cancelled = true;
        };
    }, []);

    return (
        <div className="form-group">
            <label htmlFor="integration-agent">{label}</label>
            <select
                id="integration-agent"
                className="form-input"
                value={value ?? ""}
                onChange={(e) => {
                    const val = e.target.value;
                    onChange(val ? Number(val) : null);
                }}
                disabled={loading}
            >
                <option value="">Global / not agent-specific</option>
                {agents.map((a) => (
                    <option key={a.id} value={a.id}>
                        #{a.id} — {a.name}
                    </option>
                ))}
            </select>
            {loading && (
                <div style={{ fontSize: 12, opacity: 0.7 }}>Loading agents…</div>
            )}
        </div>
    );
}
