import PageHeader from "../common/PageHeader";
import LoadingButton from "../common/LoadingButton";
import { ServerSelector } from "./ServerSelector";
import { useVeeamServer } from "../../contexts/VeeamServerContext";

interface VeeamPageShellProps {
    title: React.ReactNode;
    version?: string;
    onRefresh: () => void;
    refreshing?: boolean;
    children?: React.ReactNode;
}

export default function VeeamPageShell({
    title,
    version = "1.0",
    onRefresh,
    refreshing = false,
    children,
}: VeeamPageShellProps) {
    const { servers, selectedServerId } = useVeeamServer();

    const serverName =
        servers.length > 0
            ? servers.find((s) => s.id === selectedServerId)?.name ?? "Veeam Server"
            : "Veeam Server";

    return (
        <>
            <PageHeader
                title={title}
                subtitle={`${serverName} v${version}`}
                actions={
                    <LoadingButton
                        loading={refreshing}
                        onClick={onRefresh}
                        className="btn btn-secondary"
                        title="Refresh data"
                    >
                        Refresh
                    </LoadingButton>
                }
            />
            <ServerSelector />
            {children}
        </>
    );
}
