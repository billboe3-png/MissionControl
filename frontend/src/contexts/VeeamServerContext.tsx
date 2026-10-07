import { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from "react";
import { apiClient } from "../utils/apiClient";
import { VEEAM_SERVER_MISSING_EVENT } from "../services/veeam";
import { useAuth } from "./AuthContext";

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
    const { token } = useAuth();
    const [servers, setServers] = useState<VeeamServerConfig[]>([]);
    const [selectedServerId, setSelectedServerId] = useState<number | null>(() => {
        const stored = typeof window !== "undefined" ? localStorage.getItem("veeam.selectedServerId") : null;
        return stored ? parseInt(stored, 10) : null;
    });
    const [loading, setLoading] = useState(true);
    const fetchingRef = useRef(false);

    const fetchServers = useCallback(async () => {
        if (fetchingRef.current) return;
        fetchingRef.current = true;
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
            fetchingRef.current = false;
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        // Only fetch Veeam servers when authenticated. The provider wraps the
        // whole app (including the login page), so without this guard an
        // unauthenticated request would 401 and trigger a hard reload loop
        // through the apiClient session-expired redirect.
        if (token) {
            void fetchServers();
        } else {
            setLoading(false);
        }

        // Persist selection on change
        const handleStorage = () => {
            const stored = typeof window !== "undefined" ? localStorage.getItem("veeam.selectedServerId") : null;
            const parsed = stored ? parseInt(stored, 10) : null;
            setSelectedServerId((current) => (parsed === current ? current : parsed));
        };
        window.addEventListener("storage", handleStorage);

        // A page just got "Veeam server not found" for the id it holds: the
        // row was deleted (host removed / re-registered under another agent)
        // while the page was open. Reload the list so the selection below can
        // move onto a server that still exists.
        const handleMissing = () => {
            void fetchServers();
        };
        window.addEventListener(VEEAM_SERVER_MISSING_EVENT, handleMissing);

        return () => {
            window.removeEventListener("storage", handleStorage);
            window.removeEventListener(VEEAM_SERVER_MISSING_EVENT, handleMissing);
        };
    }, [fetchServers, token]);

    // Keep the selection pointing at an enabled server: a deleted, disabled or
    // moved host must not leave pages pinned to an id the backend rejects with
    // 404.
    useEffect(() => {
        if (servers.length === 0) {
            setSelectedServerId((current) => (current === null ? current : null));
            return;
        }
        const selected = servers.find((s) => s.id === selectedServerId);
        if (selected && selected.enabled) return;
        const firstEnabled = servers.find((s) => s.enabled);
        const next = firstEnabled ? firstEnabled.id : null;
        setSelectedServerId((current) => (current === next ? current : next));
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