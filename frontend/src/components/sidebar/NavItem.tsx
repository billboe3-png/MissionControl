import { NavLink } from "react-router-dom";
import { NavItem as NavItemType } from "../../types/navigation";

export default function NavItem({ item }: { item: NavItemType }) {
    return (
        <NavLink
            to={item.path}
            end={item.path === "/"}
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
