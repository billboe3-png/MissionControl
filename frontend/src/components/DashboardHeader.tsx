interface DashboardHeaderProps {
    name: string;
    tagline: string;
    version: string;
    generated: string;
    onRefresh: () => void;
    refreshing: boolean;
}

function formatTimestamp(iso: string): string {
    const date = new Date(iso);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

export default function DashboardHeader({
    name,
    tagline,
    version,
    generated,
    onRefresh,
    refreshing,
}: DashboardHeaderProps) {
    return (
        <header className="page-header">
            <div className="header-top">
                <div>
                    <h1>{name}</h1>
                    <p>{tagline}</p>
                    <small>Version {version}</small>
                </div>
                <div className="header-actions">
                    <span className="generated-timestamp">
                        Updated: {formatTimestamp(generated)}
                    </span>
                    <button
                        className="refresh-button"
                        onClick={onRefresh}
                        disabled={refreshing}
                    >
                        {refreshing ? "Refreshing..." : "Refresh Dashboard"}
                    </button>
                </div>
            </div>
        </header>
    );
}
