import { NavLink } from "react-router-dom";
import { NavItem as NavItemType } from "../../types/navigation";

export default function NavItem({
    item,
    collapsed,
}: {
    item: NavItemType;
    collapsed?: boolean;
}) {
    return (
        <NavLink
            to={item.path}
            end={item.path === "/"}
            data-tooltip={collapsed ? item.label : undefined}
            className={({ isActive }) =>
                `sidebar-nav-item${isActive ? " active" : ""}${item.disabled ? " disabled" : ""}`
            }
        >
            <span className="sidebar-nav-icon">{item.icon}</span>
            <span className="sidebar-nav-label">{item.label}</span>
            {item.badge && (
                <span className="sidebar-nav-badge">{item.badge}</span>
            )}
        </NavLink>
    );
}
