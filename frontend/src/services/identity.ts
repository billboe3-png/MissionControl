import { api } from "./api";

const API_BASE = "/api/v1/identity";

export interface IdentityOverview {
    ad_domain_controllers: number;
    ad_users_total: number;
    ad_computers_total: number;
    ad_groups_total: number;
    ad_gpos_total: number;
    m365_total_users: number;
    m365_licensed_users: number;
    m365_overall_status: string;
    m365_active_incidents: number;
    m365_secure_score: number;
}

export interface DomainController {
    name: string;
    ip_address: string;
    os_version: string;
    site: string;
    is_global_catalog: boolean;
    is_fsmo: boolean;
    status: string;
    last_replication: string | null;
}

export interface Forest {
    name: string;
    functional_level: string;
    domain_count: number;
    domains: string[];
    global_catalog_count: number;
    site_count: number;
    sites: string[];
    schema_master: string;
    naming_master: string;
}

export interface PasswordPolicy {
    min_length: number;
    max_age_days: number;
    history_count: number;
    complexity_required: boolean;
    lockout_threshold: number;
    lockout_duration_minutes: number;
}

export interface Domain {
    name: string;
    netbios_name: string;
    functional_level: string;
    sid: string;
    pdc_emulator: string;
    rid_master: string;
    infrastructure_master: string;
    domain_controllers: number;
    user_count: number;
    computer_count: number;
    group_count: number;
    ou_count: number;
    password_policy: PasswordPolicy;
}

export interface OrganizationalUnit {
    name: string;
    distinguished_name: string;
    path: string;
    user_count: number;
    computer_count: number;
    group_count: number;
    child_ou_count: number;
    gpo_count: number;
}

export interface UserSummary {
    sam_account_name: string;
    display_name: string;
    email: string | null;
    department: string;
    title: string;
    enabled: boolean;
    locked_out: boolean;
    password_expired: boolean;
    last_logon: string | null;
    created_at: string;
    ou: string;
}

export interface GroupSummary {
    name: string;
    sam_account_name: string;
    scope: string;
    category: string;
    member_count: number;
    description: string | null;
    is_domain_local: boolean;
    managed_by: string | null;
}

export interface ComputerSummary {
    name: string;
    dns_name: string;
    ip_address: string;
    os_version: string;
    enabled: boolean;
    last_logon: string | null;
    password_last_changed: string | null;
    ou: string;
    is_domain_controller: boolean;
}

export interface GPO {
    name: string;
    guid: string;
    description: string | null;
    version: number;
    enabled: boolean;
    linked_ous: string[];
    computer_count: number;
    user_count: number;
    created_at: string;
    modified_at: string | null;
}

export interface FSMORoleHolder {
    role: string;
    holder: string;
    status: string;
}

export interface FSMORoles {
    forest_roles: Record<string, FSMORoleHolder>;
    domain_roles: Record<string, FSMORoleHolder>;
    all_roles_held_by_single_dc: boolean;
}

export interface DNSServer {
    name: string;
    ip_address: string;
    status: string;
    zones_count: number;
    records_count: number;
    forwarders: string[];
    response_time_ms: number;
}

export interface DNSHealth {
    status: string;
    servers: DNSServer[];
    total_zones: number;
    total_records: number;
    dnssec_enabled: boolean;
}

export interface DHCPServer {
    name: string;
    ip_address: string;
    status: string;
    scopes_count: number;
    total_addresses: number;
    used_addresses: number;
    available_addresses: number;
    utilization_percent: number;
}

export interface DHCPHealth {
    status: string;
    servers: DHCPServer[];
    total_scopes: number;
    total_addresses: number;
    total_used: number;
    total_available: number;
    overall_utilization_percent: number;
    authorized: boolean;
}

export interface Microsoft365Tenant {
    id: string;
    name: string;
    display_name: string;
    domain: string;
    verified_domains: string[];
    default_domain: string;
    tenant_type: string;
    created_at: string;
    created_by: string;
    directory_sync_enabled: boolean;
    directory_sync_last_sync: string | null;
    mfa_enabled: boolean;
    conditional_access_enabled: boolean;
    total_users: number;
    licensed_users: number;
    total_groups: number;
    total_devices: number;
}

export interface LicenseSummary {
    sku_part_number: string;
    display_name: string;
    total_licenses: number;
    assigned_licenses: number;
    available_licenses: number;
    cost_per_user_monthly: number;
    total_monthly_cost: number;
}

export interface ServiceIssue {
    title: string;
    status: string;
    impact: string;
    start_time: string;
    last_update: string | null;
}

export interface ServiceHealthEntry {
    name: string;
    status: string;
    feature: string;
    issues: ServiceIssue[];
}

export interface ServiceHealth {
    overall_status: string;
    services: ServiceHealthEntry[];
    active_incidents: number;
    resolved_last_30_days: number;
}

export interface EntraHealth {
    status: string;
    sign_in_success_rate: number;
    total_sign_ins_24h: number;
    failed_sign_ins_24h: number;
    mfa_success_rate: number;
    conditional_access_policies: number;
    active_policies: number;
    blocked_sign_ins_24h: number;
    risk_detections_24h: number;
    risky_users: number;
    deleted_objects_30d: number;
    password_reset_registrations: number;
    self_service_password_resets_30d: number;
}

export interface ExchangeHealth {
    status: string;
    mailboxes_total: number;
    mailboxes_active: number;
    mailboxes_online: number;
    daily_emails_sent: number;
    daily_emails_received: number;
    average_mailbox_size_gb: number;
    total_mailbox_size_gb: number;
    dags_count: number;
    databases_count: number;
    database_availability: number;
    queue_length: number;
    transport_rules_count: number;
    connectors_count: number;
}

export interface SecureScoreCategory {
    name: string;
    current_score: number;
    max_score: number;
    percentage: number;
}

export interface SecureScore {
    current_score: number;
    max_score: number;
    percentage: number;
    comparison_to_industry: {
        your_score: number;
        average_score: number;
        tier: string;
    };
    categories: SecureScoreCategory[];
    recommended_actions_count: number;
    high_priority_actions: number;
    last_calculated: string | null;
}

export interface MessageCenterItem {
    id: string;
    title: string;
    category: string;
    severity: string;
    message: string;
    action_required: boolean;
    published_at: string;
    end_of_rollout: string | null;
    affected_services: string[];
    compatibility_impact: string;
}

async function get<T>(path: string): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) {
        throw new Error(`Identity API error: ${response.status}`);
    }
    return response.json();
}

export const identityApi = {
    getOverview: () => get<IdentityOverview>("/overview"),

    getDomainControllers: () => get<{ success: boolean; domain_controllers: DomainController[]; total_count: number }>("/ad/domain-controllers"),
    getForest: () => get<{ success: boolean; forest: Forest }>("/ad/forest"),
    getDomain: () => get<{ success: boolean; domain: Domain }>("/ad/domain"),
    getOUs: () => get<{ success: boolean; organizational_units: OrganizationalUnit[]; total_count: number }>("/ad/ous"),
    getUsers: () => get<{ success: boolean; users: UserSummary[]; total_count: number; enabled_count: number; disabled_count: number; locked_out_count: number; password_expired_count: number }>("/ad/users"),
    getGroups: () => get<{ success: boolean; groups: GroupSummary[]; total_count: number }>("/ad/groups"),
    getComputers: () => get<{ success: boolean; computers: ComputerSummary[]; total_count: number; enabled_count: number; disabled_count: number; server_count: number; workstation_count: number }>("/ad/computers"),
    getGPOs: () => get<{ success: boolean; gpos: GPO[]; total_count: number; enabled_count: number; disabled_count: number }>("/ad/gpos"),
    getFSMORoles: () => get<{ success: boolean; fsmo_roles: FSMORoles }>("/ad/fsmo-roles"),
    getDNSHealth: () => get<{ success: boolean; dns_health: DNSHealth }>("/ad/dns-health"),
    getDHCPHealth: () => get<{ success: boolean; dhcp_health: DHCPHealth }>("/ad/dhcp-health"),

    getTenant: () => get<{ success: boolean; tenant: Microsoft365Tenant }>("/m365/tenant"),
    getLicenses: () => get<{ success: boolean; licenses: LicenseSummary[]; total_sku_count: number; total_assigned: number; total_available: number; total_monthly_cost: number }>("/m365/licenses"),
    getServiceHealth: () => get<{ success: boolean; service_health: ServiceHealth }>("/m365/service-health"),
    getEntraHealth: () => get<{ success: boolean; entra_health: EntraHealth }>("/m365/entra-health"),
    getExchangeHealth: () => get<{ success: boolean; exchange_health: ExchangeHealth }>("/m365/exchange-health"),
    getSecureScore: () => get<{ success: boolean; secure_score: SecureScore }>("/m365/secure-score"),
    getMessageCenter: () => get<{ total_items: number; items: MessageCenterItem[] }>("/m365/message-center"),
};
