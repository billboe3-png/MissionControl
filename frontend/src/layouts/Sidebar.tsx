import { useLocation } from "react-router-dom";
import { useSidebar } from "../contexts/SidebarContext";
import { useAuth } from "../contexts/AuthContext";
import { navigation } from "../config/navigation";
import NavGroup from "../components/sidebar/NavGroup";
import UserBadge from "../components/sidebar/UserBadge";

function LogoutButton() {
    const { logout } = useAuth();
    return (
        <button
            className="btn btn-sm btn-outline"
            onClick={logout}
            title="Log out"
        >
            Logout
        </button>
    );
}

export default function Sidebar() {
    const { collapsed, toggle } = useSidebar();
    const location = useLocation();

    return (
        <aside className={`sidebar${collapsed ? " collapsed" : ""}`}>
            <div className="sidebar-header">
                <span className="sidebar-logo">⚡</span>
                {!collapsed && <span className="sidebar-title">Mission Control</span>}
            </div>

            <nav className="sidebar-nav">
                {navigation.map((group) => (
                    <NavGroup
                        key={group.label}
                        group={group}
                        collapsed={collapsed}
                    />
                ))}
            </nav>

            <div className="sidebar-footer">
                <UserBadge />
                <LogoutButton />
                <button
                    className="sidebar-collapse-btn"
                    onClick={toggle}
                    title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
                >
                    {collapsed ? "»" : "«"}
                </button>
            </div>
        </aside>
    );
}
