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
import IdentityOverviewPage from "./pages/identity/IdentityOverviewPage";
import ActiveDirectoryPage from "./pages/identity/ActiveDirectoryPage";
import Microsoft365Page from "./pages/identity/Microsoft365Page";
import GeneralPage from "./pages/settings/GeneralPage";
import AppearancePage from "./pages/settings/AppearancePage";
import AboutPage from "./pages/settings/AboutPage";
import ZabbixOverviewPage from "./pages/zabbix/OverviewPage";
import ZabbixHostsPage from "./pages/zabbix/HostsPage";
import ZabbixProblemsPage from "./pages/zabbix/ProblemsPage";
import ZabbixTriggersPage from "./pages/zabbix/TriggersPage";
import ZabbixEventsPage from "./pages/zabbix/EventsPage";
import ZabbixHostGroupsPage from "./pages/zabbix/HostGroupsPage";
import ZabbixTemplatesPage from "./pages/zabbix/TemplatesPage";
import ZabbixItemsPage from "./pages/zabbix/ItemsPage";
import ZabbixMapsPage from "./pages/zabbix/MapsPage";
import ZabbixDashboardsPage from "./pages/zabbix/DashboardsPage";
import ZabbixHealthPage from "./pages/zabbix/HealthPage";
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

                            <Route path="/monitoring" element={<ZabbixOverviewPage />} />
                            <Route path="/monitoring/hosts" element={<ZabbixHostsPage />} />
                            <Route path="/monitoring/problems" element={<ZabbixProblemsPage />} />
                            <Route path="/monitoring/triggers" element={<ZabbixTriggersPage />} />
                            <Route path="/monitoring/events" element={<ZabbixEventsPage />} />
                            <Route path="/monitoring/host-groups" element={<ZabbixHostGroupsPage />} />
                            <Route path="/monitoring/templates" element={<ZabbixTemplatesPage />} />
                            <Route path="/monitoring/items" element={<ZabbixItemsPage />} />
                            <Route path="/monitoring/maps" element={<ZabbixMapsPage />} />
                            <Route path="/monitoring/dashboards" element={<ZabbixDashboardsPage />} />
                            <Route path="/monitoring/health" element={<ZabbixHealthPage />} />

                            <Route path="/identity" element={<IdentityOverviewPage />} />
                            <Route path="/identity/active-directory" element={<ActiveDirectoryPage />} />
                            <Route path="/identity/microsoft-365" element={<Microsoft365Page />} />

                            <Route path="/settings" element={<GeneralPage />} />
                            <Route path="/settings/appearance" element={<AppearancePage />} />
                            <Route path="/settings/about" element={<AboutPage />} />

                            <Route path="/automation" element={<PlaceholderPage title="Automation" />} />
                            <Route path="/ai-ops" element={<PlaceholderPage title="AI Ops" />} />
                        </Route>
                    </Routes>
                </ToastProvider>
            </SidebarProvider>
        </BrowserRouter>
    );
}
