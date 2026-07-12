export default function LoadingSkeleton() {
    return (
        <main className="dashboard">
            <header className="page-header">
                <div className="skeleton skeleton-title" />
                <div className="skeleton skeleton-subtitle" />
            </header>

            <section className="dashboard-grid">
                {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="card skeleton-card">
                        <div className="skeleton skeleton-heading" />
                        <div className="skeleton skeleton-line" />
                        <div className="skeleton skeleton-line" />
                        <div className="skeleton skeleton-line short" />
                    </div>
                ))}
            </section>
        </main>
    );
}
