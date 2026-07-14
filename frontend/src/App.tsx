import { BrowserRouter, Routes, Route } from "react-router-dom";
import { SidebarProvider } from "./contexts/SidebarContext";
import { ToastProvider } from "./contexts/ToastContext";
import AppLayout from "./layouts/AppLayout";
import DashboardPage from "./pages/DashboardPage";
import OverviewPage from "./pages/infrastructure/OverviewPage";
import SystemPage from "./pages/infrastructure/SystemPage";
import DockerPage from "./pages/infrastructure/DockerPage";
import GitPage from "./pages/infrastructure/GitPage";
import HealthPage from "./pages/infrastructure/HealthPage";
import HostsPage from "./pages/remote/HostsPage";
import CredentialsPage from "./pages/remote/CredentialsPage";
import ExecutePage from "./pages/remote/ExecutePage";
import HistoryPage from "./pages/remote/HistoryPage";
import FileBrowserPage from "./pages/remote/FileBrowserPage";
import GeneralPage from "./pages/settings/GeneralPage";
import AppearancePage from "./pages/settings/AppearancePage";
import AboutPage from "./pages/settings/AboutPage";
import PlaceholderPage from "./pages/PlaceholderPage";

export default function App() {
    return (
        <BrowserRouter>
            <SidebarProvider>
                <ToastProvider>
                    <Routes>
                        <Route element={<AppLayout />}>
                            <Route path="/" element={<DashboardPage />} />

                            <Route path="/infrastructure" element={<OverviewPage />} />
                            <Route path="/infrastructure/system" element={<SystemPage />} />
                            <Route path="/infrastructure/docker" element={<DockerPage />} />
                            <Route path="/infrastructure/git" element={<GitPage />} />
                            <Route path="/infrastructure/health" element={<HealthPage />} />

                            <Route path="/remote/hosts" element={<HostsPage />} />
                            <Route path="/remote/credentials" element={<CredentialsPage />} />
                            <Route path="/remote/execute" element={<ExecutePage />} />
                            <Route path="/remote/history" element={<HistoryPage />} />
                            <Route path="/remote/files" element={<FileBrowserPage />} />

                            <Route path="/monitoring" element={<PlaceholderPage title="Monitoring" />} />

                            <Route path="/settings" element={<GeneralPage />} />
                            <Route path="/settings/appearance" element={<AppearancePage />} />
                            <Route path="/settings/about" element={<AboutPage />} />

                            <Route path="/identity" element={<PlaceholderPage title="Identity & Access" />} />
                            <Route path="/automation" element={<PlaceholderPage title="Automation" />} />
                            <Route path="/ai-ops" element={<PlaceholderPage title="AI Ops" />} />
                        </Route>
                    </Routes>
                </ToastProvider>
            </SidebarProvider>
        </BrowserRouter>
    );
}
