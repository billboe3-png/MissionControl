import { useLocation } from "react-router-dom";
import { useSidebar } from "../contexts/SidebarContext";
import { navigation } from "../config/navigation";
import NavGroup from "../components/sidebar/NavGroup";
import UserBadge from "../components/sidebar/UserBadge";

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
