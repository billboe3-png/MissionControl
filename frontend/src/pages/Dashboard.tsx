import { useEffect, useState } from "react";
import { api, DashboardResponse } from "../services/api";

export default function Dashboard() {
    const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        loadDashboard();
    }, []);

    async function loadDashboard() {
        try {
            setLoading(true);

            const data = await api.getDashboard();

            setDashboard(data);
            setError("");
        } catch (err) {
            console.error(err);
            setError("Unable to connect to the Mission Control API.");
        } finally {
            setLoading(false);
        }
    }

    if (loading) {
        return (
            <main className="dashboard">
                <h1>Mission Control</h1>
                <p>Loading dashboard...</p>
            </main>
        );
    }

    if (error) {
        return (
            <main className="dashboard">
                <h1>Mission Control</h1>

                <div className="card error-card">
                    <h2>Connection Error</h2>
                    <p>{error}</p>
                </div>
            </main>
        );
    }

    if (!dashboard) {
        return null;
    }

    const docker = dashboard.integrations.docker;
    const summary = dashboard.summary;

    return (
        <main className="dashboard">

            <header className="page-header">
                <h1>{dashboard.application.name}</h1>

                <p>{dashboard.application.tagline}</p>

                <small>
                    Version {dashboard.application.version}
                </small>
            </header>

            <section className="dashboard-grid">

                <div className="card">
                    <h2>Infrastructure Health</h2>

                    <ul className="status-list">
                        <li>
                            Backend
                            <span>{dashboard.health.backend.status}</span>
                        </li>

                        <li>
                            PostgreSQL
                            <span>{dashboard.health.database.status}</span>
                        </li>

                        <li>
                            Redis
                            <span>{dashboard.health.redis.status}</span>
                        </li>
                    </ul>
                </div>

                <div className="card">
                    <h2>Operations Overview</h2>

                    <ul className="status-list">
                        <li>
                            Running Containers
                            <span>{summary.containers_running}</span>
                        </li>

                        <li>
                            Total Projects
                            <span>{summary.projects}</span>
                        </li>

                        <li>
                            Open Tasks
                            <span>{summary.tasks}</span>
                        </li>

                        <li>
                            Notes
                            <span>{summary.notes}</span>
                        </li>

                        <li>
                            Resume Available
                            <span>{summary.resume_available ? "Yes" : "No"}</span>
                        </li>

                        <li>
                            Docker Engine
                            <span>{summary.docker_engine}</span>
                        </li>
                    </ul>
                </div>

                <div className="card">
                    <h2>Docker</h2>

                    <ul className="status-list">
                        <li>
                            Engine
                            <span>{docker.engine}</span>
                        </li>

                        <li>
                            Containers
                            <span>{docker.container_count}</span>
                        </li>

                        <li>
                            Version
                            <span>{docker.docker_version}</span>
                        </li>
                    </ul>

                    <hr />

                    {docker.containers.length === 0 ? (
                        <p>No running containers.</p>
                    ) : (
                        <ul className="status-list">
                            {docker.containers.map((container) => (
                                <li key={container.id}>
                                    {container.name}
                                    <span>{container.status}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div className="card">
                    <h2>Resume</h2>

                    {dashboard.resume.available ? (
                        <>
                            <strong>{dashboard.resume.title}</strong>
                            <p>{dashboard.resume.description}</p>
                        </>
                    ) : (
                        <p>No work currently waiting to be resumed.</p>
                    )}
                </div>

            </section>

        </main>
    );
}