import { apiClient } from "../utils/apiClient";

const API_BASE = "/api/v1/identity";

export interface ConnectionTestResult {
    connected: boolean;
    latency_ms: number | null;
    message: string | null;
    error: string | null;
}

export interface IdentityOverviewADEntry {
    profile_id: number;
    profile_name: string;
    connected: boolean;
    domain: string;
    user_count: number;
    group_count: number;
    computer_count: number;
    health: string;
    replication: {
        status: string;
        pending_replications: number;
        failed_replications: number;
    };
}

export interface IdentityOverview {
    success: boolean;
    overview: {
        ad: IdentityOverviewADEntry[];
        m365: {
            connected: boolean;
            tenant: string;
            licensed_users: number;
            license_count: number;
            health: string;
            active_incidents: number;
        };
    };
}

export interface ADUser {
    sam_account_name: string;
    display_name: string;
    email: string | null;
    department: string | null;
    title: string | null;
    enabled: boolean;
    distinguished_name: string | null;
}

export interface ADGroup {
    name: string;
    description: string | null;
}

export interface ADDevice {
    name: string;
    dns_name: string | null;
    os_version: string | null;
}

export interface ADSummary {
    connected: boolean;
    domain: { name: string | null; base_dn: string | null };
    user_count: number;
    group_count: number;
    computer_count: number;
    error: string | null;
}

export interface ADUsersResponse {
    connected: boolean;
    users: ADUser[];
    total_count: number;
    error: string | null;
}

export interface ADGroupsResponse {
    connected: boolean;
    groups: ADGroup[];
    total_count: number;
    error: string | null;
}

export interface ADDevicesResponse {
    connected: boolean;
    devices: ADDevice[];
    total_count: number;
    error: string | null;
}

export interface ADReplication {
    status: string;
    pending_replications: number;
    failed_replications: number;
}

export interface ADHealthResponse {
    connected: boolean;
    status: string;
    replication: ADReplication;
    error: string | null;
}

export interface ADActionResponse {
    success: boolean;
    message: string | null;
    error: string | null;
}

export interface ADUserGroup {
    name: string;
    dn: string;
}

export interface ADUserGroupsResponse {
    connected: boolean;
    groups: ADUserGroup[];
    error: string | null;
}

export interface ADDomainProfile {
    id: number;
    name: string;
    domain: string | null;
    base_dn: string | null;
    enabled: boolean;
}

export interface M365TenantInfo {
    id: string | null;
    display_name: string | null;
    verified_domains: string[];
    tenant_type: string | null;
}

export interface M365License {
    sku: string;
    name: string;
    assigned: number;
    total: number;
    available: number;
    status: string | null;
}

export interface M365Summary {
    connected: boolean;
    tenant: M365TenantInfo;
    licensed_users: number;
    licenses: M365License[];
    domains: string[] | null;
    error: string | null;
}

export interface M365User {
    id: string | null;
    display_name: string;
    email: string | null;
    department: string | null;
    job_title: string | null;
    account_enabled: boolean;
    licensed: boolean;
}

export interface M365UsersResponse {
    connected: boolean;
    users: M365User[];
    total_count: number;
    error: string | null;
}

export interface M365Group {
    display_name: string;
    mail: string | null;
    type: string;
}

export interface M365GroupsResponse {
    connected: boolean;
    groups: M365Group[];
    total_count: number;
    error: string | null;
}

export interface M365Device {
    id: string | null;
    name: string | null;
    display_name: string | null;
    os: string | null;
    version: string | null;
    compliant: boolean;
}

export interface M365DevicesResponse {
    connected: boolean;
    devices: M365Device[];
    total_count: number;
    error: string | null;
}

export interface M365ServiceHealthEntry {
    name: string;
    status: string;
}

export interface M365HealthResponse {
    connected: boolean;
    status: string;
    services: M365ServiceHealthEntry[];
    active_incidents: number;
    error: string | null;
}

export const identityApi = {
    getOverview: () => apiClient<IdentityOverview>(`${API_BASE}/overview`),

    getADDomains: () => apiClient<ADDomainProfile[]>(`${API_BASE}/ad/domains`),

    testAD: (profileId?: number) =>
        apiClient<ConnectionTestResult>(
            `${API_BASE}/ad/test${profileId ? `?profile_id=${profileId}` : ""}`
        ),
    getADSummary: (profileId?: number) =>
        apiClient<ADSummary>(
            `${API_BASE}/ad/summary${profileId ? `?profile_id=${profileId}` : ""}`
        ),
    getADUsers: (profileId?: number) =>
        apiClient<ADUsersResponse>(
            `${API_BASE}/ad/users${profileId ? `?profile_id=${profileId}` : ""}`
        ),
    getADGroups: (profileId?: number) =>
        apiClient<ADGroupsResponse>(
            `${API_BASE}/ad/groups${profileId ? `?profile_id=${profileId}` : ""}`
        ),
    getADDevices: (profileId?: number) =>
        apiClient<ADDevicesResponse>(
            `${API_BASE}/ad/devices${profileId ? `?profile_id=${profileId}` : ""}`
        ),
    getADHealth: (profileId?: number) =>
        apiClient<ADHealthResponse>(
            `${API_BASE}/ad/health${profileId ? `?profile_id=${profileId}` : ""}`
        ),

    resetPassword: (sam_account_name: string, new_password: string, profileId?: number) =>
        apiClient<ADActionResponse>(
            `${API_BASE}/ad/users/reset-password${profileId ? `?profile_id=${profileId}` : ""}`,
            { method: "POST", json: { sam_account_name, new_password } },
        ),
    unlockAccount: (sam_account_name: string, profileId?: number) =>
        apiClient<ADActionResponse>(
            `${API_BASE}/ad/users/unlock${profileId ? `?profile_id=${profileId}` : ""}`,
            { method: "POST", json: { sam_account_name } },
        ),
    enableAccount: (sam_account_name: string, profileId?: number) =>
        apiClient<ADActionResponse>(
            `${API_BASE}/ad/users/enable${profileId ? `?profile_id=${profileId}` : ""}`,
            { method: "POST", json: { sam_account_name } },
        ),
    disableAccount: (sam_account_name: string, profileId?: number) =>
        apiClient<ADActionResponse>(
            `${API_BASE}/ad/users/disable${profileId ? `?profile_id=${profileId}` : ""}`,
            { method: "POST", json: { sam_account_name } },
        ),
    renameUser: (sam_account_name: string, display_name: string, first_name?: string, last_name?: string, profileId?: number) =>
        apiClient<ADActionResponse>(
            `${API_BASE}/ad/users/rename${profileId ? `?profile_id=${profileId}` : ""}`,
            { method: "POST", json: { sam_account_name, display_name, first_name, last_name } },
        ),
    getUserGroups: (sam_account_name: string, profileId?: number) =>
        apiClient<ADUserGroupsResponse>(
            `${API_BASE}/ad/users/${encodeURIComponent(sam_account_name)}/groups${profileId ? `?profile_id=${profileId}` : ""}`,
        ),
    addToGroup: (sam_account_name: string, group_name: string, profileId?: number) =>
        apiClient<ADActionResponse>(
            `${API_BASE}/ad/users/add-to-group${profileId ? `?profile_id=${profileId}` : ""}`,
            { method: "POST", json: { sam_account_name, group_name } },
        ),
    removeFromGroup: (sam_account_name: string, group_name: string, profileId?: number) =>
        apiClient<ADActionResponse>(
            `${API_BASE}/ad/users/remove-from-group${profileId ? `?profile_id=${profileId}` : ""}`,
            { method: "POST", json: { sam_account_name, group_name } },
        ),

    getM365Domains: () => apiClient<ADDomainProfile[]>(`${API_BASE}/m365/domains`),

    testM365: (profileId?: number) =>
        apiClient<ConnectionTestResult>(
            `${API_BASE}/m365/test${profileId ? `?profile_id=${profileId}` : ""}`
        ),
    getM365Summary: (profileId?: number) =>
        apiClient<M365Summary>(
            `${API_BASE}/m365/summary${profileId ? `?profile_id=${profileId}` : ""}`
        ),
    getM365Users: (profileId?: number) =>
        apiClient<M365UsersResponse>(
            `${API_BASE}/m365/users${profileId ? `?profile_id=${profileId}` : ""}`
        ),
    getM365Groups: (profileId?: number) =>
        apiClient<M365GroupsResponse>(
            `${API_BASE}/m365/groups${profileId ? `?profile_id=${profileId}` : ""}`
        ),
    getM365Devices: (profileId?: number) =>
        apiClient<M365DevicesResponse>(
            `${API_BASE}/m365/devices${profileId ? `?profile_id=${profileId}` : ""}`
        ),
    getM365Health: (profileId?: number) =>
        apiClient<M365HealthResponse>(
            `${API_BASE}/m365/health${profileId ? `?profile_id=${profileId}` : ""}`
        ),
};
