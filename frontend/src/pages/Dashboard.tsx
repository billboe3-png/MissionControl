import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../services/api";
import { DashboardResponse } from "../types/dashboard";
import DashboardHeader from "../components/DashboardHeader";
import HealthCard from "../components/HealthCard";
import OverviewCard from "../components/OverviewCard";
import SystemCard from "../components/SystemCard";
import DockerCard from "../components/DockerCard";
import GitCard from "../components/GitCard";
import ProjectsCard from "../components/ProjectsCard";
import TasksCard from "../components/TasksCard";
import NotesCard from "../components/NotesCard";
import ResumeCard from "../components/ResumeCard";
import ParkingLotCard from "../components/ParkingLotCard";
import RemoteOperationsCard from "../components/RemoteOperationsCard";
import LoadingSkeleton from "../components/LoadingSkeleton";
import ErrorCard from "../components/ErrorCard";
import ToastContainer from "../components/Toast";
import { useToasts } from "../hooks/useToasts";

const REFRESH_INTERVAL_MS = 30_000;

export default function Dashboard() {
    const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [refreshing, setRefreshing] = useState(false);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const mountedRef = useRef(true);
    const { toasts, showToast, dismissToast } = useToasts();

    const handleDashboardData = useCallback((data: DashboardResponse) => {
        setDashboard(data);
        setError("");
    }, []);

    const handleDashboardError = useCallback((err: unknown) => {
        console.error(err);
        setError("Unable to connect to the Mission Control API.");
    }, []);

    const loadDashboard = useCallback(async () => {
        try {
            setLoading(true);
            const data = await api.getDashboard();
            handleDashboardData(data);
        } catch (err) {
            handleDashboardError(err);
        } finally {
            if (mountedRef.current) {
                setLoading(false);
            }
        }
    }, [handleDashboardData, handleDashboardError]);

    const refreshDashboard = useCallback(async () => {
        try {
            setRefreshing(true);
            const data = await api.getDashboard();
            handleDashboardData(data);
        } catch (err) {
            handleDashboardError(err);
        } finally {
            if (mountedRef.current) {
                setRefreshing(false);
            }
        }
    }, [handleDashboardData, handleDashboardError]);

    useEffect(() => {
        mountedRef.current = true;

        const initialLoad = async () => {
            try {
                const data = await api.getDashboard();
                if (mountedRef.current) {
                    handleDashboardData(data);
                }
            } catch (err) {
                if (mountedRef.current) {
                    handleDashboardError(err);
                }
            } finally {
                if (mountedRef.current) {
                    setLoading(false);
                }
            }
        };

        initialLoad();

        intervalRef.current = setInterval(() => {
            refreshDashboard();
        }, REFRESH_INTERVAL_MS);

        return () => {
            mountedRef.current = false;
            if (intervalRef.current !== null) {
                clearInterval(intervalRef.current);
            }
        };
    }, [handleDashboardData, handleDashboardError, refreshDashboard]);

    if (loading) {
        return <LoadingSkeleton />;
    }

    if (error) {
        return <ErrorCard message={error} onRetry={loadDashboard} />;
    }

    if (!dashboard) {
        return null;
    }

    return (
        <main className="dashboard">
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />

            <DashboardHeader
                name={dashboard.application.name}
                tagline={dashboard.application.tagline}
                version={dashboard.application.version}
                generated={dashboard.generated}
                onRefresh={refreshDashboard}
                refreshing={refreshing}
            />

            <section className="dashboard-grid dashboard-grid-4">
                <HealthCard health={dashboard.health} />

                <OverviewCard summary={dashboard.summary} />

                <SystemCard system={dashboard.system} />

                <GitCard git={dashboard.git} />

                <DockerCard docker={dashboard.docker} />

                <ProjectsCard
                    count={dashboard.projects.count}
                    items={dashboard.projects.items}
                    onRefresh={refreshDashboard}
                    showToast={showToast}
                />

                <TasksCard
                    count={dashboard.tasks.count}
                    items={dashboard.tasks.items}
                    projects={dashboard.projects.items}
                    onRefresh={refreshDashboard}
                    showToast={showToast}
                />

                <NotesCard
                    count={dashboard.notes.count}
                    items={dashboard.notes.items}
                    projects={dashboard.projects.items}
                    onRefresh={refreshDashboard}
                    showToast={showToast}
                />

                <ResumeCard
                    available={dashboard.resume.available}
                    title={dashboard.resume.title}
                    description={dashboard.resume.description}
                />

                <ParkingLotCard
                    count={dashboard.parking_lot.count}
                    items={dashboard.parking_lot.items}
                    onRefresh={refreshDashboard}
                    showToast={showToast}
                />

                <RemoteOperationsCard
                    totalHosts={dashboard.remote.totalHosts}
                    enabledHosts={dashboard.remote.enabledHosts}
                    recentCommands={dashboard.remote.recentCommands}
                    onRefresh={refreshDashboard}
                    showToast={showToast}
                />
            </section>
        </main>
    );
}
