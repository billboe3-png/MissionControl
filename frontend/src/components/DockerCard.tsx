import { DockerData } from "../types/dashboard";

function containerStateClass(state: string): string {
    switch (state) {
        case "running":
            return "badge badge-success";
        case "exited":
            return "badge badge-danger";
        case "created":
        case "restarting":
            return "badge badge-warning";
        default:
            return "badge badge-muted";
    }
}

interface DockerCardProps {
    docker: DockerData;
}

export default function DockerCard({ docker }: DockerCardProps) {
    return (
        <div className="card">
            <h2>Docker</h2>

            {!docker.available ? (
                <p className="muted-text">
                    Docker engine not available.
                </p>
            ) : (
                <>
                    <ul className="status-list">
                        <li>
                            Engine
                            <span>{docker.engine}</span>
                        </li>

                        <li>
                            Version
                            <span>{docker.docker_version}</span>
                        </li>

                        <li>
                            Compose
                            <span>{docker.compose_version}</span>
                        </li>

                        <li>
                            Containers
                            <span>
                                {docker.running} / {docker.container_count}
                            </span>
                        </li>

                        <li>
                            Images
                            <span>{docker.image_count}</span>
                        </li>
                    </ul>

                    {docker.containers.length > 0 && (
                        <>
                            <hr />
                            <ul className="status-list">
                                {docker.containers.map((container) => (
                                    <li key={container.id}>
                                        <span className="item-content">
                                            <strong>{container.name}</strong>
                                            <span className="item-description">
                                                {container.image}
                                            </span>
                                        </span>
                                        <span
                                            className={containerStateClass(
                                                container.state,
                                            )}
                                        >
                                            {container.state}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        </>
                    )}
                </>
            )}
        </div>
    );
}
