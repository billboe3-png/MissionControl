export interface ApplicationInfo {
    name: string;
    tagline: string;
    version: string;
}

export interface Project {
    id: number;
    name: string;
    description: string | null;
    active: boolean;
    created_at: string;
    updated_at: string;
}

export interface ProjectStatistics {
    total: number;
    active: number;
    inactive: number;
}

export interface ProjectsData {
    count: number;
    statistics: ProjectStatistics;
    items: Project[];
}

export interface Task {
    id: number;
    project_id: number;
    project_name: string;
    title: string;
    description: string | null;
    status: string;
    priority: string;
    created_at: string;
    updated_at: string;
}

export interface TaskStatistics {
    total: number;
    pending: number;
    in_progress: number;
    completed: number;
    blocked: number;
}

export interface PriorityStatistics {
    high: number;
    medium: number;
    low: number;
}

export interface TasksData {
    count: number;
    statistics: TaskStatistics;
    priority_statistics: PriorityStatistics;
    items: Task[];
}

export interface Note {
    id: number;
    project_id: number | null;
    project_name: string | null;
    title: string;
    content: string;
    created_at: string;
    updated_at: string;
}

export interface NotesData {
    count: number;
    items: Note[];
}

export interface ParkingLotItem {
    id: number;
    title: string;
    description: string | null;
    priority: string;
    status: string;
    owner: string | null;
    category: string | null;
    labels: string | null;
    target_sprint: string | null;
    archived: boolean;
    created_by: string | null;
    created_at: string;
    updated_at: string;
}

export interface ParkingLotStatistics {
    total: number;
    parked: number;
    in_progress: number;
    done: number;
    archived: number;
}

export interface ParkingLotData {
    count: number;
    statistics: ParkingLotStatistics;
    items: ParkingLotItem[];
}

export interface HealthService {
    status: string;
    message: string;
    project_count?: number;
}

export interface Health {
    backend: HealthService;
    database: HealthService;
    redis: HealthService;
}

export interface SystemInfo {
    hostname: string;
    os: string;
    platform: string;
    cpu_count: number;
    cpu_percent: number;
    memory_total: number;
    memory_used: number;
    memory_percent: number;
    disk_total: number;
    disk_used: number;
    disk_percent: number;
    uptime_seconds: number;
    boot_time: number;
}

export interface DockerContainer {
    id: string;
    name: string;
    image: string;
    status: string;
    state: string;
    cpu_percent: number | null;
    memory_percent: number | null;
    restart_count: number | null;
    ports: string[];
    health: string | null;
    created: string | null;
    uptime: string | null;
}

export interface DockerData {
    available: boolean;
    engine: string;
    docker_version: string | null;
    compose_version: string | null;
    container_count: number;
    running: number;
    stopped: number;
    image_count: number;
    containers: DockerContainer[];
}

export interface GitInfo {
    available: boolean;
    repository_name: string | null;
    current_branch: string | null;
    latest_commit: string | null;
    commit_author: string | null;
    commit_date: string | null;
    working_tree_clean: boolean;
    ahead_of_origin: number;
    behind_origin: number;
    last_pull: string | null;
    remote_url: string | null;
    reason?: string;
}

export interface Summary {
    projects: number;
    active_projects: number;
    tasks: number;
    completed_tasks: number;
    pending_tasks: number;
    notes: number;
    resume_available: boolean;
    containers_running: number;
    containers_total: number;
    docker_engine: string;
}

export interface IntegrationStatus {
    enabled: boolean;
    status: string;
}

export interface IntegrationListItem {
    id: number;
    name: string;
    type: string;
    enabled: boolean;
    connected: boolean;
    last_test: string | null;
}

export interface IntegrationListData {
    count: number;
    items: IntegrationListItem[];
}

export interface Integrations {
    docker: DockerData;
    ssh: IntegrationStatus;
    zabbix: IntegrationStatus;
    github: IntegrationStatus;
    profiles: IntegrationListData;
}

export interface RemoteCommand {
    id: number;
    host_id: number;
    command: string;
    success: boolean;
    started_at: string | null;
}

export interface RemoteData {
    totalHosts: number;
    enabledHosts: number;
    recentCommands: RemoteCommand[];
}

export interface DashboardResponse {
    application: ApplicationInfo;
    generated: string;
    summary: Summary;
    health: Health;
    system: SystemInfo;
    docker: DockerData;
    git: GitInfo;
    projects: ProjectsData;
    tasks: TasksData;
    notes: NotesData;
    resume: {
        available: boolean;
        title: string | null;
        description: string | null;
        current_sprint: string | null;
        current_goal: string | null;
        current_project: string | null;
        current_branch: string | null;
        last_activity: string | null;
    };
    parking_lot: ParkingLotData;
    remote: RemoteData;
    integrations: Integrations;
}
