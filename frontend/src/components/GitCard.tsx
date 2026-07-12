import { GitInfo } from "../types/dashboard";

function formatDate(iso: string | null): string {
    if (!iso) return "N/A";
    const date = new Date(iso);
    return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

interface GitCardProps {
    git: GitInfo;
}

export default function GitCard({ git }: GitCardProps) {
    return (
        <div className="card">
            <h2>Git Repository</h2>

            {!git.available ? (
                <p className="muted-text">
                    {git.reason || "Git repository not available."}
                </p>
            ) : (
                <ul className="status-list">
                    <li>
                        Repository
                        <span>{git.repository_name}</span>
                    </li>

                    <li>
                        Branch
                        <span>{git.current_branch}</span>
                    </li>

                    <li>
                        Latest Commit
                        <span className="mono">{git.latest_commit}</span>
                    </li>

                    <li>
                        Author
                        <span>{git.commit_author}</span>
                    </li>

                    <li>
                        Commit Date
                        <span>{formatDate(git.commit_date)}</span>
                    </li>

                    <li>
                        Working Tree
                        <span
                            className={
                                git.working_tree_clean
                                    ? "badge badge-success"
                                    : "badge badge-warning"
                            }
                        >
                            {git.working_tree_clean ? "Clean" : "Dirty"}
                        </span>
                    </li>

                    <li>
                        Ahead / Behind
                        <span>
                            {git.ahead_of_origin} / {git.behind_origin}
                        </span>
                    </li>

                    {git.remote_url && (
                        <li>
                            Remote
                            <span className="mono small-text">
                                {git.remote_url}
                            </span>
                        </li>
                    )}
                </ul>
            )}
        </div>
    );
}
