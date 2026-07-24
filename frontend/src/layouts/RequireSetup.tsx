import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { setupApi } from "../services/setup";

export default function RequireSetup() {
    const [setupRequired, setSetupRequired] = useState<boolean | null>(null);

    useEffect(() => {
        setupApi
            .getStatus()
            .then((s) => setSetupRequired(s.setup_required))
            .catch(() => setSetupRequired(false));
    }, []);

    if (setupRequired === null) return <div className="loading-bar" />;

    if (setupRequired) {
        return <Navigate to="/setup" replace />;
    }

    return <Outlet />;
}
