import { useState } from "react";
import { NavGroup as NavGroupType } from "../../types/navigation";
import NavItem from "./NavItem";

export default function NavGroup({
    group,
    collapsed,
}: {
    group: NavGroupType;
    collapsed: boolean;
}) {
    const [open, setOpen] = useState(group.defaultOpen ?? false);

    if (collapsed) {
        return (
            <div className="sidebar-nav-group collapsed">
                {group.items.map((item) => (
                    <NavItem key={item.path} item={item} />
                ))}
            </div>
        );
    }

    return (
        <div className="sidebar-nav-group">
            <button
                className="sidebar-group-header"
                onClick={() => setOpen((prev) => !prev)}
            >
                <span className="sidebar-group-icon">{group.icon}</span>
                <span className="sidebar-group-label">{group.label}</span>
                <span className={`sidebar-group-chevron${open ? " open`" : ""}`}>
                    ▾
                </span>
            </button>
            {open && (
                <div className="sidebar-group-items">
                    {group.items.map((item) => (
                        <NavItem key={item.path} item={item} />
                    ))}
                </div>
            )}
        </div>
    );
}
