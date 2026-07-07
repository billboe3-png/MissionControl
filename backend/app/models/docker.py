from pydantic import BaseModel


class ContainerSummary(BaseModel):
    running: int
    stopped: int
    paused: int
    total: int


class ContainerInfo(BaseModel):
    id: str
    name: str
    image: str
    status: str
    state: str
    created: str
    ports: list[str]
    cpu: float
    memory: float


class ImageInfo(BaseModel):
    name: str
    tag: str
    size: str


class SystemInfo(BaseModel):
    docker_version: str
    api_version: str
    os: str
    kernel: str
    cpus: int
    memory: int


class DockerResponse(BaseModel):
    enabled: bool
    summary: ContainerSummary | None = None
    containers: list[ContainerInfo] = []
    images: list[ImageInfo] = []
    system: SystemInfo | None = None
    error: str | None = None
