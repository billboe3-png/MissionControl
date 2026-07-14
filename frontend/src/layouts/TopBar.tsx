import { useLocation, useNavigate } from "react-router-dom";
import Breadcrumb from "./Breadcrumb";

export default function TopBar() {
    const location = useLocation();
    const navigate = useNavigate();

    return (
        <header className="topbar">
            <Breadcrumb path={location.pathname} />
            <div className="topbar-actions">
                <input
                    className="topbar-search"
                    type="text"
                    placeholder="Search… (Ctrl+K)"
                    onKeyDown={(e) => {
                        if (e.key === "Escape") (e.target as HTMLInputElement).blur();
                    }}
                />
            </div>
        </header>
    );
}
