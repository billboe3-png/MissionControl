import { Summary } from "../types/dashboard";

interface OverviewCardProps {
    summary: Summary;
}

export default function OverviewCard({ summary }: OverviewCardProps) {
    return (
        <div className="card">
            <h2>Operations Overview</h2>

            <ul className="status-list">
                <li>
                    Projects
                    <span>{summary.projects}</span>
                </li>

                <li>
                    Active Projects
                    <span>{summary.active_projects}</span>
                </li>

                <li>
                    Tasks
                    <span>{summary.tasks}</span>
                </li>

                <li>
                    Completed Tasks
                    <span>{summary.completed_tasks}</span>
                </li>

                <li>
                    Pending Tasks
                    <span>{summary.pending_tasks}</span>
                </li>

                <li>
                    Notes
                    <span>{summary.notes}</span>
                </li>

                <li>
                    Running Containers
                    <span>{summary.containers_running}</span>
                </li>

                <li>
                    Total Containers
                    <span>{summary.containers_total}</span>
                </li>

                <li>
                    Docker Engine
                    <span>{summary.docker_engine}</span>
                </li>

                <li>
                    Resume Available
                    <span>{summary.resume_available ? "Yes" : "No"}</span>
                </li>
            </ul>
        </div>
    );
}
