import PageHeader from "../../components/common/PageHeader";

export default function GeneralPage() {
    return (
        <>
            <PageHeader
                title="Settings"
                subtitle="General application settings"
            />
            <div className="settings-section">
                <h3>Application</h3>
                <p className="settings-hint">
                    Mission Control v1.0 — IT Operations Dashboard
                </p>
            </div>
            <div className="settings-section">
                <h3>Default View</h3>
                <p className="settings-hint">
                    The dashboard is now the default landing page.
                </p>
            </div>
        </>
    );
}
