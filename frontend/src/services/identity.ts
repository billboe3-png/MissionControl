import { api } from "./api";

const API_BASE = "/api/v1/identity";

export interface ConnectionTestResult {
    connected: boolean;
    latency_ms: number | null;
    message: string | null;
    error: string | null;
}

export interface IdentityOverview {
    success: boolean;
    overview: {
        ad: {
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
        };
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

async function get<T>(path: string): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) {
        throw new Error(`Identity API error: ${response.status}`);
    }
    return response.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!response.ok) {
        throw new Error(`Identity API error: ${response.status}`);
    }
    return response.json();
}

export const identityApi = {
    getOverview: () => get<IdentityOverview>("/overview"),

    testAD: () => get<ConnectionTestResult>("/ad/test"),
    getADSummary: () => get<ADSummary>("/ad/summary"),
    getADUsers: () => get<ADUsersResponse>("/ad/users"),
    getADGroups: () => get<ADGroupsResponse>("/ad/groups"),
    getADDevices: () => get<ADDevicesResponse>("/ad/devices"),
    getADHealth: () => get<ADHealthResponse>("/ad/health"),

    resetPassword: (sam_account_name: string, new_password: string) =>
        post<ADActionResponse>("/ad/users/reset-password", { sam_account_name, new_password }),
    unlockAccount: (sam_account_name: string) =>
        post<ADActionResponse>("/ad/users/unlock", { sam_account_name }),
    enableAccount: (sam_account_name: string) =>
        post<ADActionResponse>("/ad/users/enable", { sam_account_name }),
    disableAccount: (sam_account_name: string) =>
        post<ADActionResponse>("/ad/users/disable", { sam_account_name }),
    renameUser: (sam_account_name: string, display_name: string, first_name?: string, last_name?: string) =>
        post<ADActionResponse>("/ad/users/rename", { sam_account_name, display_name, first_name, last_name }),
    getUserGroups: (sam_account_name: string) =>
        get<ADUserGroupsResponse>(`/ad/users/${encodeURIComponent(sam_account_name)}/groups`),
    addToGroup: (sam_account_name: string, group_name: string) =>
        post<ADActionResponse>("/ad/users/add-to-group", { sam_account_name, group_name }),
    removeFromGroup: (sam_account_name: string, group_name: string) =>
        post<ADActionResponse>("/ad/users/remove-from-group", { sam_account_name, group_name }),

    testM365: () => get<ConnectionTestResult>("/m365/test"),
    getM365Summary: () => get<M365Summary>("/m365/summary"),
    getM365Users: () => get<M365UsersResponse>("/m365/users"),
    getM365Groups: () => get<M365GroupsResponse>("/m365/groups"),
    getM365Devices: () => get<M365DevicesResponse>("/m365/devices"),
    getM365Health: () => get<M365HealthResponse>("/m365/health"),
};
