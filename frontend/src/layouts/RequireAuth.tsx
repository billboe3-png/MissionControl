import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function RequireAuth() {
    const { token, loading } = useAuth();

    if (loading) return <div className="loading-bar" />;

    if (!token) {
        return <Navigate to="/login" replace />;
    }

    return <Outlet />;
}
