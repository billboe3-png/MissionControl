interface ErrorCardProps {
    message: string;
    onRetry: () => void;
}

export default function ErrorCard({ message, onRetry }: ErrorCardProps) {
    return (
        <main className="dashboard">
            <header className="page-header">
                <h1>Mission Control</h1>
                <p>The Daily Workspace for IT Operations</p>
            </header>

            <div className="card error-card">
                <h2>Connection Error</h2>
                <p>{message}</p>
                <button className="retry-button" onClick={onRetry}>
                    Retry
                </button>
            </div>
        </main>
    );
}
