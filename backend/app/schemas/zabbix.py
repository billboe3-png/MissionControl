"""
Mission Control Zabbix Schemas

Pydantic request/response models for Zabbix monitoring operations.

Sprint 2.3.0 - Enterprise Zabbix Integration.
"""

from pydantic import BaseModel

# ------------------------------------------------------------------ #
# Common                                                              #
# ------------------------------------------------------------------ #


class ZabbixConnectionTestResponse(BaseModel):
    """Response for connection test."""

    connected: bool
    latency_ms: int | None = None
    message: str | None = None
    version: str | None = None
    error: str | None = None


# ------------------------------------------------------------------ #
# Hosts                                                               #
# ------------------------------------------------------------------ #


class ZabbixHost(BaseModel):
    """Zabbix host."""

    hostid: str
    host: str
    name: str
    status: str
    available: str
    interface: str = ""
    groups: list[str] = []
    templates: list[str] = []
    last_access: str | None = None


class ZabbixHostsResponse(BaseModel):
    """Response for host listing."""

    connected: bool
    hosts: list[ZabbixHost] = []
    total_count: int = 0
    enabled_count: int = 0
    disabled_count: int = 0
    available_count: int = 0
    unavailable_count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Host Groups                                                         #
# ------------------------------------------------------------------ #


class ZabbixHostGroup(BaseModel):
    """Zabbix host group."""

    groupid: str
    name: str
    host_count: int = 0


class ZabbixHostGroupsResponse(BaseModel):
    """Response for host group listing."""

    connected: bool
    groups: list[ZabbixHostGroup] = []
    total_count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Triggers                                                            #
# ------------------------------------------------------------------ #


class ZabbixTrigger(BaseModel):
    """Zabbix trigger."""

    triggerid: str
    description: str
    status: str
    priority: str
    value: str
    hosts: list[str] = []


class ZabbixTriggersResponse(BaseModel):
    """Response for trigger listing."""

    connected: bool
    triggers: list[ZabbixTrigger] = []
    total_count: int = 0
    enabled_count: int = 0
    disabled_count: int = 0
    problem_count: int = 0
    ok_count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Problems                                                            #
# ------------------------------------------------------------------ #


class ZabbixProblem(BaseModel):
    """Zabbix problem."""

    eventid: str
    name: str
    severity: str
    status: str
    acknowledged: bool
    host: str
    timestamp: str


class ZabbixProblemsResponse(BaseModel):
    """Response for problem listing."""

    connected: bool
    problems: list[ZabbixProblem] = []
    total_count: int = 0
    severity_counts: dict[str, int] = {}
    acknowledged_count: int = 0
    unacknowledged_count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Events                                                              #
# ------------------------------------------------------------------ #


class ZabbixEvent(BaseModel):
    """Zabbix event."""

    eventid: str
    name: str
    severity: str
    status: str
    host: str
    timestamp: str


class ZabbixEventsResponse(BaseModel):
    """Response for event listing."""

    connected: bool
    events: list[ZabbixEvent] = []
    total_count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Items                                                               #
# ------------------------------------------------------------------ #


class ZabbixItem(BaseModel):
    """Zabbix item."""

    itemid: str
    name: str
    key_: str = ""
    status: str
    type: str
    last_value: str = ""
    host: str = ""


class ZabbixItemsResponse(BaseModel):
    """Response for item listing."""

    connected: bool
    items: list[ZabbixItem] = []
    total_count: int = 0
    supported_count: int = 0
    unsupported_count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Templates                                                           #
# ------------------------------------------------------------------ #


class ZabbixTemplate(BaseModel):
    """Zabbix template."""

    templateid: str
    name: str
    hosts_count: int = 0


class ZabbixTemplatesResponse(BaseModel):
    """Response for template listing."""

    connected: bool
    templates: list[ZabbixTemplate] = []
    total_count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Dashboards                                                          #
# ------------------------------------------------------------------ #


class ZabbixDashboard(BaseModel):
    """Zabbix dashboard."""

    dashboardid: str
    name: str
    display_name: str = ""
    owner: str = ""
    pages: int = 0


class ZabbixDashboardsResponse(BaseModel):
    """Response for dashboard listing."""

    connected: bool
    dashboards: list[ZabbixDashboard] = []
    total_count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Maps                                                                #
# ------------------------------------------------------------------ #


class ZabbixMap(BaseModel):
    """Zabbix map."""

    sysmapid: str
    name: str
    width: int = 0
    height: int = 0
    elements: int = 0


class ZabbixMapsResponse(BaseModel):
    """Response for map listing."""

    connected: bool
    maps: list[ZabbixMap] = []
    total_count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Health                                                              #
# ------------------------------------------------------------------ #


class ZabbixDatabaseHealth(BaseModel):
    """Zabbix database health."""

    status: str = "unknown"
    type: str = "unknown"
    size_mb: int = 0


class ZabbixHealthResponse(BaseModel):
    """Response for Zabbix health."""

    connected: bool
    status: str = "unknown"
    version: str = "unknown"
    server: str = ""
    uptime_hours: int = 0
    api_latency_ms: int = 0
    database: ZabbixDatabaseHealth = ZabbixDatabaseHealth()
    proxy_count: int = 0
    poller_items_per_sec: int = 0
    trigger_functions_per_sec: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Summary                                                             #
# ------------------------------------------------------------------ #


class ZabbixSummaryResponse(BaseModel):
    """Response for Zabbix summary."""

    connected: bool
    version: str = "unknown"
    server_name: str = ""
    host_count: int = 0
    problem_count: int = 0
    critical_count: int = 0
    warning_count: int = 0
    ok_count: int = 0
    uptime_hours: int = 0
    api_latency_ms: int = 0
    error: str | None = None
