"""
Mission Control Identity Schemas

Pydantic request/response models for Active Directory
and Microsoft 365 identity operations.

Sprint 2.2.0 - Microsoft 365 & Active Directory Integration.
"""

from pydantic import BaseModel

# ------------------------------------------------------------------ #
# Common Schemas                                                      #
# ------------------------------------------------------------------ #


class ConnectionTestResponse(BaseModel):
    """Response for connection test."""

    connected: bool
    latency_ms: int | None = None
    message: str | None = None
    error: str | None = None


# ------------------------------------------------------------------ #
# Active Directory Schemas                                            #
# ------------------------------------------------------------------ #


class ADUser(BaseModel):
    """Active Directory user summary."""

    sam_account_name: str
    display_name: str
    email: str | None = None
    department: str | None = None
    title: str | None = None
    enabled: bool
    distinguished_name: str | None = None


class ADUsersResponse(BaseModel):
    """Response for AD user listing."""

    connected: bool
    users: list[ADUser] = []
    total_count: int = 0
    error: str | None = None


class ADGroup(BaseModel):
    """Active Directory group summary."""

    name: str
    description: str | None = None


class ADGroupsResponse(BaseModel):
    """Response for AD group listing."""

    connected: bool
    groups: list[ADGroup] = []
    total_count: int = 0
    error: str | None = None


class ADDevice(BaseModel):
    """Active Directory computer/device summary."""

    name: str
    dns_name: str | None = None
    os_version: str | None = None


class ADDevicesResponse(BaseModel):
    """Response for AD device listing."""

    connected: bool
    devices: list[ADDevice] = []
    total_count: int = 0
    error: str | None = None


class ADReplication(BaseModel):
    """AD replication status."""

    status: str = "unknown"
    pending_replications: int = 0
    failed_replications: int = 0


class ADHealthResponse(BaseModel):
    """Response for AD health."""

    connected: bool
    status: str = "unknown"
    replication: ADReplication = ADReplication()
    error: str | None = None


class ADDomainInfo(BaseModel):
    """AD domain information from summary."""

    name: str | None = None
    base_dn: str | None = None


class ADSummaryResponse(BaseModel):
    """Response for AD summary."""

    connected: bool
    domain: ADDomainInfo = ADDomainInfo()
    user_count: int = 0
    group_count: int = 0
    computer_count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Microsoft 365 Schemas                                              #
# ------------------------------------------------------------------ #


class M365TenantInfo(BaseModel):
    """M365 tenant information from summary."""

    id: str | None = None
    display_name: str | None = None
    verified_domains: list[str] = []
    tenant_type: str | None = None


class M365License(BaseModel):
    """M365 license summary entry."""

    sku: str
    name: str
    assigned: int
    total: int = 0
    available: int = 0
    status: str | None = None


class M365SummaryResponse(BaseModel):
    """Response for M365 summary."""

    connected: bool
    tenant: M365TenantInfo = M365TenantInfo()
    licensed_users: int = 0
    licenses: list[M365License] = []
    domains: list[str] | None = None
    error: str | None = None


class M365User(BaseModel):
    """M365 user summary."""

    id: str | None = None
    display_name: str
    email: str | None = None
    department: str | None = None
    job_title: str | None = None
    account_enabled: bool
    licensed: bool = False


class M365UsersResponse(BaseModel):
    """Response for M365 user listing."""

    connected: bool
    users: list[M365User] = []
    total_count: int = 0
    error: str | None = None


class M365Group(BaseModel):
    """M365 group summary."""

    display_name: str
    mail: str | None = None
    type: str


class M365GroupsResponse(BaseModel):
    """Response for M365 group listing."""

    connected: bool
    groups: list[M365Group] = []
    total_count: int = 0
    error: str | None = None


class M365Device(BaseModel):
    """M365 managed device summary."""

    id: str | None = None
    name: str | None = None
    display_name: str | None = None
    os: str | None = None
    version: str | None = None
    compliant: bool = False


class M365DevicesResponse(BaseModel):
    """Response for M365 device listing."""

    connected: bool
    devices: list[M365Device] = []
    total_count: int = 0
    error: str | None = None


class M365ServiceHealth(BaseModel):
    """M365 service health entry."""

    name: str
    status: str


class M365HealthResponse(BaseModel):
    """Response for M365 health."""

    connected: bool
    status: str = "unknown"
    services: list[M365ServiceHealth] = []
    active_incidents: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# AD Write Operation Schemas                                          #
# ------------------------------------------------------------------ #


class ADPasswordResetRequest(BaseModel):
    """Request to reset a user's password."""

    sam_account_name: str
    new_password: str


class ADUnlockRequest(BaseModel):
    """Request to unlock a user account."""

    sam_account_name: str


class ADRenameRequest(BaseModel):
    """Request to rename a user."""

    sam_account_name: str
    display_name: str
    first_name: str | None = None
    last_name: str | None = None


class ADGroupMembershipRequest(BaseModel):
    """Request to add/remove a user from a group."""

    sam_account_name: str
    group_name: str


class ADActionResponse(BaseModel):
    """Generic response for AD write actions."""

    success: bool
    message: str | None = None
    error: str | None = None


class ADUserGroupsResponse(BaseModel):
    """Response for user's group membership."""

    connected: bool
    groups: list[dict] = []
    error: str | None = None


# ------------------------------------------------------------------ #
# Combined Overview                                                   #
# ------------------------------------------------------------------ #


class IdentityOverviewAD(BaseModel):
    """AD section of identity overview."""

    connected: bool = False
    domain: str = "N/A"
    user_count: int = 0
    group_count: int = 0
    computer_count: int = 0
    health: str = "unknown"
    replication: ADReplication = ADReplication()


class IdentityOverviewM365(BaseModel):
    """M365 section of identity overview."""

    connected: bool = False
    tenant: str = "N/A"
    licensed_users: int = 0
    license_count: int = 0
    health: str = "unknown"
    active_incidents: int = 0


class IdentityOverviewResponse(BaseModel):
    """Combined identity overview for the dashboard."""

    success: bool
    overview: dict
