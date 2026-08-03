import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { SidebarProvider } from "./contexts/SidebarContext";
import { ToastProvider } from "./contexts/ToastContext";
import AppLayout from "./layouts/AppLayout";
import RequireAuth from "./layouts/RequireAuth";
import RequireSetup from "./layouts/RequireSetup";
import LoginPage from "./pages/auth/LoginPage";
import SetupWizardPage from "./pages/setup/SetupWizardPage";
import DashboardPage from "./pages/DashboardPage";
import OverviewPage from "./pages/infrastructure/OverviewPage";
import SystemPage from "./pages/infrastructure/SystemPage";
import HealthPage from "./pages/infrastructure/HealthPage";
import HostsPage from "./pages/remote/HostsPage";
import CredentialsPage from "./pages/remote/CredentialsPage";
import ExecutePage from "./pages/remote/ExecutePage";
import ConsolePage from "./pages/remote/ConsolePage";
import HistoryPage from "./pages/remote/HistoryPage";
import FileBrowserPage from "./pages/remote/FileBrowserPage";
import QuickCommandsPage from "./pages/remote/QuickCommandsPage";
import IdentityOverviewPage from "./pages/identity/IdentityOverviewPage";
import ActiveDirectoryPage from "./pages/identity/ActiveDirectoryPage";
import Microsoft365Page from "./pages/identity/Microsoft365Page";
import GeneralPage from "./pages/settings/GeneralPage";
import UsersPage from "./pages/settings/UsersPage";
import IntegrationsPage from "./pages/settings/IntegrationsPage";
import AppearancePage from "./pages/settings/AppearancePage";
import AboutPage from "./pages/settings/AboutPage";
import PersonalDashboardPage from "./pages/settings/PersonalDashboardPage";
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
import ZabbixServersPage from "./pages/monitoring/ZabbixServersPage";
import HyperVOverviewPage from "./pages/hyperv/OverviewPage";
import VirtualMachinesPage from "./pages/hyperv/VirtualMachinesPage";
import NetworksPage from "./pages/hyperv/NetworksPage";
import StoragePage from "./pages/hyperv/StoragePage";
import CheckpointsPage from "./pages/hyperv/CheckpointsPage";
import HyperVReplicationPage from "./pages/hyperv/ReplicationPage";
import HyperVHealthPage from "./pages/hyperv/HealthPage";
import ProxmoxOverviewPage from "./pages/proxmox/OverviewPage";
import ProxmoxHealthPage from "./pages/proxmox/HealthPage";
import ProxmoxNodesPage from "./pages/proxmox/NodesPage";
import ProxmoxVirtualMachinesPage from "./pages/proxmox/VirtualMachinesPage";
import ProxmoxContainersPage from "./pages/proxmox/ContainersPage";
import ProxmoxStoragePage from "./pages/proxmox/StoragePage";
import ProxmoxNetworksPage from "./pages/proxmox/NetworksPage";
import ProxmoxTasksPage from "./pages/proxmox/TasksPage";
import ProxmoxSnapshotsPage from "./pages/proxmox/SnapshotsPage";
import VeeamOverviewPage from "./pages/veeam/OverviewPage";
import VeeamHealthPage from "./pages/veeam/HealthPage";
import VeeamJobsPage from "./pages/veeam/JobsPage";
import VeeamSessionsPage from "./pages/veeam/SessionsPage";
import VeeamRepositoriesPage from "./pages/veeam/RepositoriesPage";
import VeeamServersPage from "./pages/veeam/ServersPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import AIOverviewPage from "./pages/ai/OverviewPage";
import AIRecommendationsPage from "./pages/ai/RecommendationsPage";
import AIIncidentAnalysisPage from "./pages/ai/IncidentAnalysisPage";
import AICorrelationsPage from "./pages/ai/CorrelationsPage";
import AIHealthScorePage from "./pages/ai/HealthScorePage";
import AIHistoryPage from "./pages/ai/HistoryPage";
import CompaniesPage from "./pages/companies/CompaniesPage";
import ProjectsPage from "./pages/projects/ProjectsPage";
import ResumesPage from "./pages/resume/ResumesPage";
import CompanyDetailPage from "./pages/companies/CompanyDetailPage";
import CompanyWorkspacePage from "./pages/companies/CompanyWorkspacePage";
import TimelinePage from "./pages/remote/TimelinePage";
import CommandCenterPage from "./pages/remote/CommandCenterPage";
import HealthCenterPage from "./pages/plugins/HealthCenterPage";
import PluginCenterPage from "./pages/plugins/PluginCenterPage";
import AutomationOverviewPage from "./pages/automation/OverviewPage";
import PlaybooksPage from "./pages/automation/PlaybooksPage";
import PlaybookDetailPage from "./pages/automation/PlaybookDetailPage";
import ExecutionsPage from "./pages/automation/ExecutionsPage";
import ApprovalsPage from "./pages/automation/ApprovalsPage";
import SchedulesPage from "./pages/automation/SchedulesPage";
import TriggersPage from "./pages/automation/TriggersPage";
import AuditPage from "./pages/automation/AuditPage";
import AgentsOverviewPage from "./pages/agents/AgentsOverviewPage";
import AgentDetailPage from "./pages/agents/AgentDetailPage";
import AgentInstallPage from "./pages/agents/AgentInstallPage";
import UniFiDashboardPage from "./pages/unifi/DashboardPage";
import UniFiDevicesPage from "./pages/unifi/DevicesPage";
import UniFiClientsPage from "./pages/unifi/ClientsPage";
import UniFiAlertsPage from "./pages/unifi/AlertsPage";
import UniFiWirelessPage from "./pages/unifi/WirelessPage";
import UniFiControllersPage from "./pages/unifi/ControllersPage";
import UniFiSitesPage from "./pages/unifi/SitesPage";
import NetworkTopologyPage from "./pages/network/NetworkTopologyPage";

export default function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <SidebarProvider>
                    <ToastProvider>
                        <Routes>
                            <Route path="/setup" element={<SetupWizardPage />} />
                            <Route element={<RequireSetup />}>
                                <Route path="/login" element={<LoginPage />} />
                            </Route>
                            <Route element={<RequireAuth />}>
                            <Route element={<AppLayout />}>
                            <Route path="/" element={<DashboardPage />} />

                            <Route path="/infrastructure" element={<OverviewPage />} />
                            <Route path="/infrastructure/system" element={<SystemPage />} />
                            <Route path="/infrastructure/health" element={<HealthPage />} />

                            <Route path="/remote/hosts" element={<HostsPage />} />
                            <Route path="/remote/credentials" element={<CredentialsPage />} />
                            <Route path="/remote/console" element={<ConsolePage />} />
                            <Route path="/remote/execute" element={<ExecutePage />} />
                            <Route path="/remote/quick-commands" element={<QuickCommandsPage />} />
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
                            <Route path="/monitoring/servers" element={<ZabbixServersPage />} />

                            <Route path="/identity" element={<IdentityOverviewPage />} />
                            <Route path="/identity/active-directory" element={<ActiveDirectoryPage />} />
                            <Route path="/identity/microsoft-365" element={<Microsoft365Page />} />

                            <Route path="/projects" element={<ProjectsPage />} />
                            <Route path="/resume" element={<ResumesPage />} />
                            <Route path="/companies" element={<CompaniesPage />} />
                            <Route path="/companies/:id" element={<CompanyDetailPage />} />

                            <Route path="/hyperv" element={<HyperVOverviewPage />} />
                            <Route path="/hyperv/vms" element={<VirtualMachinesPage />} />
                            <Route path="/hyperv/networks" element={<NetworksPage />} />
                            <Route path="/hyperv/storage" element={<StoragePage />} />
                            <Route path="/hyperv/checkpoints" element={<CheckpointsPage />} />
                            <Route path="/hyperv/replication" element={<HyperVReplicationPage />} />
                            <Route path="/hyperv/health" element={<HyperVHealthPage />} />

                            <Route path="/proxmox" element={<ProxmoxOverviewPage />} />
                            <Route path="/proxmox/health" element={<ProxmoxHealthPage />} />
                            <Route path="/proxmox/nodes" element={<ProxmoxNodesPage />} />
                            <Route path="/proxmox/vms" element={<ProxmoxVirtualMachinesPage />} />
                            <Route path="/proxmox/lxc" element={<ProxmoxContainersPage />} />
                            <Route path="/proxmox/storage" element={<ProxmoxStoragePage />} />
                            <Route path="/proxmox/networks" element={<ProxmoxNetworksPage />} />
                            <Route path="/proxmox/snapshots" element={<ProxmoxSnapshotsPage />} />
                            <Route path="/proxmox/tasks" element={<ProxmoxTasksPage />} />

                            {/* Veeam */}
                            <Route path="/veeam" element={<VeeamOverviewPage />} />
                            <Route path="/veeam/health" element={<VeeamHealthPage />} />
                            <Route path="/veeam/jobs" element={<VeeamJobsPage />} />
                            <Route path="/veeam/sessions" element={<VeeamSessionsPage />} />
                            <Route path="/veeam/repositories" element={<VeeamRepositoriesPage />} />

                            <Route path="/veeam/servers" element={<VeeamServersPage />} />

                            {/* Network */}
                            <Route path="/network/topology" element={<NetworkTopologyPage />} />

                            {/* UniFi */}
                            <Route path="/unifi" element={<UniFiDashboardPage />} />
                            <Route path="/unifi/devices" element={<UniFiDevicesPage />} />
                            <Route path="/unifi/clients" element={<UniFiClientsPage />} />
                            <Route path="/unifi/alerts" element={<UniFiAlertsPage />} />
                            <Route path="/unifi/wireless" element={<UniFiWirelessPage />} />
                            <Route path="/unifi/controllers" element={<UniFiControllersPage />} />
                            <Route path="/unifi/sites" element={<UniFiSitesPage />} />

                            <Route path="/settings" element={<GeneralPage />} />
                            <Route path="/settings/users" element={<UsersPage />} />
                            <Route path="/settings/integrations" element={<IntegrationsPage />} />
                            <Route path="/settings/appearance" element={<AppearancePage />} />
                            <Route path="/settings/about" element={<AboutPage />} />
                            <Route path="/settings/dashboard" element={<PersonalDashboardPage />} />

                            <Route path="/agents" element={<AgentsOverviewPage />} />
                            <Route path="/agents/:id" element={<AgentDetailPage />} />
                            <Route path="/agents/install" element={<AgentInstallPage />} />

                            <Route path="/fleet" element={<AgentsOverviewPage />} />
                            <Route path="/fleet/timeline" element={<TimelinePage />} />
                            <Route path="/fleet/commands" element={<CommandCenterPage />} />
                            <Route path="/fleet/health" element={<HealthCenterPage />} />
                            <Route path="/fleet/plugins" element={<PluginCenterPage />} />
                            <Route path="/fleet/companies" element={<CompanyWorkspacePage />} />

                            <Route path="/automation" element={<AutomationOverviewPage />} />
                            <Route path="/automation/playbooks" element={<PlaybooksPage />} />
                            <Route path="/automation/playbooks/new" element={<PlaybookDetailPage />} />
                            <Route path="/automation/playbooks/:id" element={<PlaybookDetailPage />} />
                            <Route path="/automation/playbooks/:id/steps/new" element={<PlaybookDetailPage />} />
                            <Route path="/automation/executions" element={<ExecutionsPage />} />
                            <Route path="/automation/approvals" element={<ApprovalsPage />} />
                            <Route path="/automation/schedules" element={<SchedulesPage />} />
                            <Route path="/automation/triggers" element={<TriggersPage />} />
                            <Route path="/automation/audit" element={<AuditPage />} />

                            <Route path="/ai" element={<AIOverviewPage />} />
                            <Route path="/ai/recommendations" element={<AIRecommendationsPage />} />
                            <Route path="/ai/incidents" element={<AIIncidentAnalysisPage />} />
                            <Route path="/ai/correlations" element={<AICorrelationsPage />} />
                            <Route path="/ai/health" element={<AIHealthScorePage />} />
                            <Route path="/ai/history" element={<AIHistoryPage />} />
                        </Route>
                        </Route>
                        </Routes>
                    </ToastProvider>
                </SidebarProvider>
            </AuthProvider>
        </BrowserRouter>
    );
}
