"""
Mission Control Veeam B&R Schemas

Pydantic request/response models for the Veeam Backup & Replication API.
"""

from pydantic import BaseModel

# ------------------------------------------------------------------ #
# Connection                                                          #
# ------------------------------------------------------------------ #


class VeeamConnectionTestResponse(BaseModel):
    connected: bool
    version: str | None = None
    name: str | None = None
    server_id: str | None = None
    error: str | None = None


# ------------------------------------------------------------------ #
# Summary                                                             #
# ------------------------------------------------------------------ #


class VeeamSummaryResponse(BaseModel):
    success: bool
    version: str | None = None
    name: str | None = None
    total_jobs: int = 0
    running_jobs: int = 0
    total_repositories: int = 0
    total_space_bytes: int = 0
    used_space_bytes: int = 0
    recent_sessions: int = 0
    sessions_success: int = 0
    sessions_warning: int = 0
    sessions_failed: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Jobs                                                                #
# ------------------------------------------------------------------ #


class VeeamJobListResponse(BaseModel):
    success: bool
    jobs: list[dict] = []
    server_names: list[str] = []
    count: int = 0
    error: str | None = None


class VeeamJobDetailResponse(BaseModel):
    success: bool
    job: dict | None = None
    error: str | None = None


class VeeamJobActionResponse(BaseModel):
    success: bool
    message: str | None = None
    error: str | None = None


# ------------------------------------------------------------------ #
# Sessions                                                            #
# ------------------------------------------------------------------ #


class VeeamSessionListResponse(BaseModel):
    success: bool
    sessions: list[dict] = []
    server_names: list[str] = []
    count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Repositories                                                        #
# ------------------------------------------------------------------ #


class VeeamRepositoryListResponse(BaseModel):
    success: bool
    repositories: list[dict] = []
    count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Managed servers                                                     #
# ------------------------------------------------------------------ #


class VeeamManagedServerListResponse(BaseModel):
    success: bool
    servers: list[dict] = []
    count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Restore points                                                      #
# ------------------------------------------------------------------ #


class VeeamRestorePointListResponse(BaseModel):
    success: bool
    restore_points: list[dict] = []
    count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# License                                                             #
# ------------------------------------------------------------------ #


class VeeamLicenseResponse(BaseModel):
    success: bool
    license: dict | None = None
    error: str | None = None


# ------------------------------------------------------------------ #
# Capacity tier                                                       #
# ------------------------------------------------------------------ #


class VeeamCapacityTierResponse(BaseModel):
    success: bool
    object_storages: list[dict] = []
    count: int = 0
    error: str | None = None


# ------------------------------------------------------------------ #
# Health                                                              #
# ------------------------------------------------------------------ #


class VeeamHealthResponse(BaseModel):
    healthy: bool
    version: str | None = None
    name: str | None = None
    error: str | None = None


class VeeamSessionStatsResponse(BaseModel):
    success: bool
    stats: list[dict] = []
    server_names: list[str] = []
    ssh_available: bool = False
    count: int = 0
    message: str | None = None
    error: str | None = None


class VeeamJobStatsResponse(BaseModel):
    success: bool
    jobs: list[dict] = []
    server_names: list[str] = []
    ssh_available: bool = False
    count: int = 0
    message: str | None = None
    error: str | None = None


class VeeamJobStatsDailyResponse(BaseModel):
    success: bool
    jobs: list[dict] = []
    dates: list[str] = []
    server_names: list[str] = []
    ssh_available: bool = False
    count: int = 0
    message: str | None = None
    error: str | None = None
