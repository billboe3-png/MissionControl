import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { apiClient } from "../utils/apiClient";

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
                const configList = await apiClient<VeeamServerConfig[]>(
                    "/api/v1/plugins/veeam/servers/config",
                );
                setServers(configList);
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