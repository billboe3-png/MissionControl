import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { companiesApi } from "../services/company";

interface SiteContextValue {
    timezone: string;
    loading: boolean;
}

const SiteContext = createContext<SiteContextValue>({ timezone: "UTC", loading: true });

export { SiteContext };

export function SiteProvider({ children }: { children: ReactNode }) {
    const [timezone, setTimezone] = useState("UTC");
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const list = await companiesApi.list();
                const first = list[0];
                if (first && first.timezone && !cancelled) {
                    setTimezone(first.timezone);
                }
            } catch {
                // keep default UTC
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, []);

    return (
        <SiteContext.Provider value={{ timezone, loading }}>
            {children}
        </SiteContext.Provider>
    );
}

export function useSiteTimezone(): string {
    return useContext(SiteContext).timezone;
}

export function useSiteLoading(): boolean {
    return useContext(SiteContext).loading;
}
