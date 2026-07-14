import StatusBadge from "../common/StatusBadge";
import { CommandHistoryData } from "../../services/remote";

export default function RecentCommands({
    items,
}: {
    items: CommandHistoryData[];
}) {
    if (items.length === 0) {
        return <p className="recent-commands-empty">No recent commands</p>;
    }

    return (
        <div className="recent-commands">
            {items.map((cmd) => (
                <div key={cmd.id} className="recent-command-item">
                    <code className="recent-command-text">{cmd.command}</code>
                    <StatusBadge
                        status={cmd.success ? "healthy" : "error"}
                        label={cmd.success ? "OK" : "FAIL"}
                    />
                </div>
            ))}
        </div>
    );
}
