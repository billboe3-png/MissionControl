import { useVeeamServer } from "../../contexts/VeeamServerContext";
import { VeeamServerConfig } from "../../contexts/VeeamServerContext";

interface ServerSelectorProps {
    className?: string;
    style?: React.CSSProperties;
}

export function ServerSelector({ className, style }: ServerSelectorProps) {
    const { servers, selectedServerId, setSelectedServerId } = useVeeamServer();

    // Hidden entirely if zero or one server (single-server installs get no UI churn)
    if (servers.length <= 1) {
        return null;
    }

    const selectedServer = servers.find((s) => s.id === selectedServerId);

    return (
        <div
            style={{
                ...style,
                ...(className && { className }),
            }}
        >
            <select
                value={selectedServerId ?? ""}
                onChange={(e) => setSelectedServerId(Number(e.target.value) || null)}
                style={{
                    padding: "0.3rem 0.5rem",
                    borderRadius: "4px",
                    border: "1px solid #30363d",
                    background: "#0d1117",
                    color: "#c9d1d9",
                    fontSize: "0.85rem",
                    cursor: "pointer",
                    appearance: "none",
                    WebkitAppearance: "none",
                    MozAppearance: "none",
                }}
            >
                <option value="" disabled>
                    Select server
                </option>
                {servers.map((server) => {
                    const isSelected = server.id === selectedServerId;
                    return (
                        <option
                            key={server.id}
                            value={server.id}
                            style={{
                                background: isSelected ? "#1a3a5c" : "#161b22",
                                color: isSelected ? "#b8d4f0" : "#8b949e",
                            }}
                        >
                            {server.name}
                        </option>
                    );
                })}
            </select>
        </div>
    );
}