import { createContext, useContext, useState, useEffect, ReactNode } from "react";

export interface VeeamServerConfig {
    id: number;
    name: string;
    url: string;
    username: string;
    verify_ssl: boolean;
    timeout: number;
    enabled: boolean;
    ssh_host: string | null;
    ssh_port: number;
    ssh_username: string | null;
    data_source: string;
    db_type: string;
    column_case: string;
}

export interface VeeamServerContextValue {
    servers: VeeamServerConfig[];
    selectedServerId: number | null;
    setSelectedServerId: (id: number | null) => void;
    loading: boolean;
}

const VeeamServerContext = createContext<VeeamServerContextValue | undefined>(undefined);

export const useVeeamServer = (): VeeamServerContextValue => {
    const context = useContext(VeeamServerContext);
    if (!context) {
        throw new Error("useVeeamServer must be used within a VeeamServerProvider");
    }
    return context;
};

export const VeeamServerProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [servers, setServers] = useState<VeeamServerConfig[]>([]);
    const [selectedServerId, setSelectedServerId] = useState<number | null>(() => {
        const stored = typeof window !== "undefined" ? localStorage.getItem("veeam.selectedServerId") : null;
        return stored ? parseInt(stored, 10) : null;
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchServers() {
            setLoading(true);
            try {
                // Try to fetch remote targets from the agent remote target API
                // This lists targets for the authenticated agent
                const result = await fetch("/api/v1/agents/remote-targets", {
                    credentials: "include",
                });
                
                if (result.ok) {
                    const targets: any[] = await result.json();
                    
                    // Filter targets that have the Veeam plugin "tick" enabled
                    // target_plugins should contain 'veeam' and enabled should be true
                    const veeamTargets = targets.filter((t: any) => 
                        t.target_plugins && t.target_plugins.includes("veeam") && t.enabled
                    );

                    // Convert remote targets to VeeamServerConfig objects
                    const configList: VeeamServerConfig[] = veeamTargets.map((t: any) => ({
                        id: t.id,
                        name: t.name,
                        url: t.hostname || "",
                        username: t.username || "",
                        verify_ssl: true,
                        timeout: 30,
                        enabled: t.enabled,
                        ssh_host: t.hostname || null,
                        ssh_port: t.port || 22,
                        ssh_username: t.username || null,
                        data_source: "ssh",
                        db_type: "postgresql",
                        column_case: "pascal",
                    }));

                    setServers(configList);
                } else {
                    // Fallback: fetch from the servers config API
                    const configResult = await fetch("/api/v1/plugins/veeam/servers/config", {
                        credentials: "include",
                    });
                    if (configResult.ok) {
                        const configList: VeeamServerConfig[] = await configResult.json();
                        setServers(configList);
                    } else {
                        setServers([]);
                    }
                }
            } catch (e) {
                console.error("Failed to fetch Veeam servers:", e);
                setServers([]);
            } finally {
                setLoading(false);
            }
        }

        fetchServers();

        // Persist selection on change
        const handleStorage = () => {
            const stored = typeof window !== "undefined" ? localStorage.getItem("veeam.selectedServerId") : null;
            const parsed = stored ? parseInt(stored, 10) : null;
            if (parsed !== selectedServerId) {
                setSelectedServerId(parsed);
            }
        };
        window.addEventListener("storage", handleStorage);
        return () => window.removeEventListener("storage", handleStorage);
    }, [selectedServerId]);

    // When servers change, if the current selection is no longer valid, reset to first enabled
    useEffect(() => {
        if (servers.length > 0 && !servers.some((s) => s.id === selectedServerId)) {
            const firstEnabled = servers.find((s) => s.enabled);
            setSelectedServerId(firstEnabled ? firstEnabled.id : servers[0].id);
        }
    }, [servers, selectedServerId]);

    return (
        <VeeamServerContext.Provider value={{ servers, selectedServerId, setSelectedServerId, loading }}>
            {children}
        </VeeamServerContext.Provider>
    );
};

export const VeeamServerContextProvider: React.FC<{ children: ReactNode }> = ({
    children,
}) => <VeeamServerProvider>{children}</VeeamServerProvider>;