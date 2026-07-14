import PageHeader from "../../components/common/PageHeader";

export default function AboutPage() {
    return (
        <>
            <PageHeader
                title="About"
                subtitle="Mission Control"
            />
            <div className="settings-section">
                <h3>Version</h3>
                <p>Mission Control v1.0.0</p>
            </div>
            <div className="settings-section">
                <h3>Built With</h3>
                <ul className="about-stack">
                    <li>FastAPI + SQLAlchemy + PostgreSQL</li>
                    <li>React 18 + TypeScript + Vite</li>
                    <li>Tailwind CSS</li>
                </ul>
            </div>
            <div className="settings-section">
                <h3>UI Architecture</h3>
                <p>
                    Inspired by Windows Admin Center. Persistent sidebar with
                    collapsible navigation groups, breadcrumb navigation, and
                    a status bar with live clock.
                </p>
            </div>
        </>
    );
}
