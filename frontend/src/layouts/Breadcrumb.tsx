import { Link } from "react-router-dom";

const routeLabels: Record<string, string> = {
    "": "Dashboard",
    infrastructure: "Infrastructure",
    system: "System",
    health: "Health",
    remote: "Remote Operations",
    hosts: "Hosts",
    credentials: "Credentials",
    console: "Console",
    execute: "Execute",
    "quick-commands": "Quick Commands",
    history: "History",
    files: "File Browser",
    settings: "Settings",
    appearance: "Appearance",
    about: "About",
};

export default function Breadcrumb({ path }: { path: string }) {
    const segments = path.split("/").filter(Boolean);

    if (segments.length === 0) {
        return (
            <nav className="breadcrumb">
                <span className="breadcrumb-item active">Dashboard</span>
            </nav>
        );
    }

    return (
        <nav className="breadcrumb">
            <Link to="/" className="breadcrumb-item">
                Dashboard
            </Link>
            {segments.map((segment, i) => {
                const subPath = "/" + segments.slice(0, i + 1).join("/");
                const label = routeLabels[segment] ?? segment;
                const isLast = i === segments.length - 1;

                return (
                    <span key={subPath} className="breadcrumb-separator">
                        <span className="breadcrumb-chevron">›</span>
                        {isLast ? (
                            <span className="breadcrumb-item active">{label}</span>
                        ) : (
                            <Link to={subPath} className="breadcrumb-item">
                                {label}
                            </Link>
                        )}
                    </span>
                );
            })}
        </nav>
    );
}
