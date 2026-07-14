import PageHeader from "../../components/common/PageHeader";

export default function AppearancePage() {
    return (
        <>
            <PageHeader
                title="Appearance"
                subtitle="Visual preferences"
            />
            <div className="settings-section">
                <h3>Theme</h3>
                <p className="settings-hint">
                    Dark theme is the default. More themes coming in a future sprint.
                </p>
            </div>
        </>
    );
}
