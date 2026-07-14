"""
Mission Control Identity Schemas

Pydantic request/response models for Active Directory
and Microsoft 365 identity operations.

Sprint 2.2.1 - Identity Platform Foundation.
"""

from pydantic import BaseModel

# ------------------------------------------------------------------ #
# Active Directory Schemas                                            #
# ------------------------------------------------------------------ #


class DomainController(BaseModel):
    """Domain controller summary."""

    name: str
    ip_address: str
    os_version: str
    site: str
    is_global_catalog: bool
    is_fsmo: bool
    status: str
    last_replication: str | None = None


class DomainControllerResponse(BaseModel):
    """Response for domain controller listing."""

    success: bool
    domain_controllers: list[DomainController]
    total_count: int


class Forest(BaseModel):
    """Forest information."""

    name: str
    functional_level: str
    domain_count: int
    domains: list[str]
    global_catalog_count: int
    site_count: int
    sites: list[str]
    schema_master: str
    naming_master: str


class ForestResponse(BaseModel):
    """Response for forest information."""

    success: bool
    forest: Forest


class PasswordPolicy(BaseModel):
    """Domain password policy."""

    min_length: int
    max_age_days: int
    history_count: int
    complexity_required: bool
    lockout_threshold: int
    lockout_duration_minutes: int


class Domain(BaseModel):
    """Domain information."""

    name: str
    netbios_name: str
    functional_level: str
    sid: str
    pdc_emulator: str
    rid_master: str
    infrastructure_master: str
    domain_controllers: int
    user_count: int
    computer_count: int
    group_count: int
    ou_count: int
    password_policy: PasswordPolicy


class DomainResponse(BaseModel):
    """Response for domain information."""

    success: bool
    domain: Domain


class OrganizationalUnit(BaseModel):
    """Organizational unit summary."""

    name: str
    distinguished_name: str
    path: str
    user_count: int
    computer_count: int
    group_count: int
    child_ou_count: int
    gpo_count: int


class OrganizationalUnitResponse(BaseModel):
    """Response for organizational unit listing."""

    success: bool
    organizational_units: list[OrganizationalUnit]
    total_count: int


class UserSummary(BaseModel):
    """Active Directory user summary."""

    sam_account_name: str
    display_name: str
    email: str | None = None
    department: str
    title: str
    enabled: bool
    locked_out: bool
    password_expired: bool
    last_logon: str | None = None
    created_at: str
    ou: str


class UserSummaryResponse(BaseModel):
    """Response for user listing."""

    success: bool
    users: list[UserSummary]
    total_count: int
    enabled_count: int
    disabled_count: int
    locked_out_count: int
    password_expired_count: int


class GroupSummary(BaseModel):
    """Active Directory group summary."""

    name: str
    sam_account_name: str
    scope: str
    category: str
    member_count: int
    description: str | None = None
    is_domain_local: bool
    managed_by: str | None = None


class GroupSummaryResponse(BaseModel):
    """Response for group listing."""

    success: bool
    groups: list[GroupSummary]
    total_count: int


class ComputerSummary(BaseModel):
    """Active Directory computer summary."""

    name: str
    dns_name: str
    ip_address: str
    os_version: str
    enabled: bool
    last_logon: str | None = None
    password_last_changed: str | None = None
    ou: str
    is_domain_controller: bool


class ComputerSummaryResponse(BaseModel):
    """Response for computer listing."""

    success: bool
    computers: list[ComputerSummary]
    total_count: int
    enabled_count: int
    disabled_count: int
    server_count: int
    workstation_count: int


class GPO(BaseModel):
    """Group Policy Object summary."""

    name: str
    guid: str
    description: str | None = None
    version: int
    enabled: bool
    linked_ous: list[str]
    computer_count: int
    user_count: int
    created_at: str
    modified_at: str | None = None


class GPOResponse(BaseModel):
    """Response for GPO listing."""

    success: bool
    gpos: list[GPO]
    total_count: int
    enabled_count: int
    disabled_count: int


class FSMORoleHolder(BaseModel):
    """FSMO role holder."""

    role: str
    holder: str
    status: str


class FSMORoles(BaseModel):
    """FSMO role information."""

    forest_roles: dict[str, FSMORoleHolder]
    domain_roles: dict[str, FSMORoleHolder]
    all_roles_held_by_single_dc: bool


class FSMORoleResponse(BaseModel):
    """Response for FSMO roles."""

    success: bool
    fsmo_roles: FSMORoles


class DNSServer(BaseModel):
    """DNS server health entry."""

    name: str
    ip_address: str
    status: str
    zones_count: int
    records_count: int
    forwarders: list[str]
    response_time_ms: int


class DNSHealth(BaseModel):
    """DNS health information."""

    status: str
    servers: list[DNSServer]
    total_zones: int
    total_records: int
    dnssec_enabled: bool


class DNSHealthResponse(BaseModel):
    """Response for DNS health."""

    success: bool
    dns_health: DNSHealth


class DHCPServer(BaseModel):
    """DHCP server health entry."""

    name: str
    ip_address: str
    status: str
    scopes_count: int
    total_addresses: int
    used_addresses: int
    available_addresses: int
    utilization_percent: float


class DHCPHealth(BaseModel):
    """DHCP health information."""

    status: str
    servers: list[DHCPServer]
    total_scopes: int
    total_addresses: int
    total_used: int
    total_available: int
    overall_utilization_percent: float
    authorized: bool


class DHCPHealthResponse(BaseModel):
    """Response for DHCP health."""

    success: bool
    dhcp_health: DHCPHealth


# ------------------------------------------------------------------ #
# Microsoft 365 Schemas                                              #
# ------------------------------------------------------------------ #


class Microsoft365Tenant(BaseModel):
    """Microsoft 365 tenant information."""

    id: str
    name: str
    display_name: str
    domain: str
    verified_domains: list[str]
    default_domain: str
    tenant_type: str
    created_at: str
    created_by: str
    directory_sync_enabled: bool
    directory_sync_last_sync: str | None = None
    mfa_enabled: bool
    conditional_access_enabled: bool
    total_users: int
    licensed_users: int
    total_groups: int
    total_devices: int


class TenantResponse(BaseModel):
    """Response for tenant information."""

    success: bool
    tenant: Microsoft365Tenant


class LicenseSummary(BaseModel):
    """License summary entry."""

    sku_part_number: str
    display_name: str
    total_licenses: int
    assigned_licenses: int
    available_licenses: int
    cost_per_user_monthly: float
    total_monthly_cost: float


class LicenseSummaryResponse(BaseModel):
    """Response for license listing."""

    success: bool
    licenses: list[LicenseSummary]
    total_sku_count: int
    total_assigned: int
    total_available: int
    total_monthly_cost: float


class ServiceIssue(BaseModel):
    """Service health issue."""

    title: str
    status: str
    impact: str
    start_time: str
    last_update: str | None = None


class ServiceHealthEntry(BaseModel):
    """Individual service health entry."""

    name: str
    status: str
    feature: str
    issues: list[ServiceIssue]


class ServiceHealth(BaseModel):
    """Microsoft 365 service health overview."""

    overall_status: str
    services: list[ServiceHealthEntry]
    active_incidents: int
    resolved_last_30_days: int


class ServiceHealthResponse(BaseModel):
    """Response for service health."""

    success: bool
    service_health: ServiceHealth


class EntraHealth(BaseModel):
    """Entra ID health information."""

    status: str
    sign_in_success_rate: float
    total_sign_ins_24h: int
    failed_sign_ins_24h: int
    mfa_success_rate: float
    conditional_access_policies: int
    active_policies: int
    blocked_sign_ins_24h: int
    risk_detections_24h: int
    risky_users: int
    deleted_objects_30d: int
    password_reset_registrations: int
    self_service_password_resets_30d: int


class EntraHealthResponse(BaseModel):
    """Response for Entra health."""

    success: bool
    entra_health: EntraHealth


class ExchangeHealth(BaseModel):
    """Exchange Online health information."""

    status: str
    mailboxes_total: int
    mailboxes_active: int
    mailboxes_online: int
    daily_emails_sent: int
    daily_emails_received: int
    average_mailbox_size_gb: float
    total_mailbox_size_gb: float
    dags_count: int
    databases_count: int
    database_availability: float
    queue_length: int
    transport_rules_count: int
    connectors_count: int


class ExchangeHealthResponse(BaseModel):
    """Response for Exchange health."""

    success: bool
    exchange_health: ExchangeHealth


class SecureScoreComparison(BaseModel):
    """Secure Score comparison to industry."""

    your_score: float
    average_score: float
    tier: str


class SecureScoreCategory(BaseModel):
    """Secure Score category breakdown."""

    name: str
    current_score: float
    max_score: float
    percentage: float


class SecureScore(BaseModel):
    """Secure Score overview."""

    current_score: float
    max_score: float
    percentage: float
    comparison_to_industry: SecureScoreComparison
    categories: list[SecureScoreCategory]
    recommended_actions_count: int
    high_priority_actions: int
    last_calculated: str | None = None


class SecureScoreResponse(BaseModel):
    """Response for Secure Score."""

    success: bool
    secure_score: SecureScore


class MessageCenterItem(BaseModel):
    """Message Center item."""

    id: str
    title: str
    category: str
    severity: str
    message: str
    action_required: bool
    published_at: str
    end_of_rollout: str | None = None
    affected_services: list[str]
    compatibility_impact: str


class MessageCenterResponse(BaseModel):
    """Response for Message Center."""

    total_items: int
    items: list[MessageCenterItem]


class IdentityOverviewResponse(BaseModel):
    """Combined identity overview for the dashboard."""

    ad_domain_controllers: int
    ad_users_total: int
    ad_computers_total: int
    ad_groups_total: int
    ad_gpos_total: int
    m365_total_users: int
    m365_licensed_users: int
    m365_overall_status: str
    m365_active_incidents: int
    m365_secure_score: float
