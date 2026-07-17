# Plugin SDK

The Plugin SDK defines the public interfaces that all plugins must use. Plugins must never access private interfaces or bypass the SDK.

## Base Classes

### PluginSDK (Abstract)

All plugins extend `PluginSDK`. Provides lifecycle methods and shared utilities.

```python
class PluginSDK(ABC):
    def __init__(self, manifest: dict, config: dict): ...
    
    @property
    def slug(self) -> str: ...
    @property
    def version(self) -> str: ...
    @property
    def execution_target(self) -> str: ...
    
    @abstractmethod
    async def setup(self) -> None: ...
    @abstractmethod
    async def start(self) -> None: ...
    @abstractmethod
    async def stop(self) -> None: ...
    
    async def on_enable(self) -> None: ...
    async def on_disable(self) -> None: ...
    async def on_config_changed(self, new_config: dict) -> None: ...
    async def health_check(self) -> dict: ...
    async def get_capabilities(self) -> list[str]: ...
    def get_config(self, key: str, default=None): ...
    def require_config(self, key: str): ...
```

### ServerPluginSDK

Extends `PluginSDK` with server-side extension points.

**Extension Points:**
- `get_dashboard_widgets()` — Register dashboard widgets
- `get_widget_data(widget_id)` — Provide data for a widget
- `get_routes()` — Register additional REST API routes
- `get_navigation_items()` — Add sidebar navigation items
- `get_settings_schema()` — Define plugin settings UI
- `get_settings()` / `save_settings()` — Read/write settings
- `get_providers()` — Offer provider implementations
- `send_notification()` — Send notifications
- `get_scheduled_jobs()` — Register background jobs
- `get_models()` — Register additional database models
- `get_migrations()` — Provide Alembic migrations

### AgentPluginSDK

Extends `PluginSDK` with agent-side capabilities.

**Capabilities:**
- `get_commands()` — Register executable commands
- `execute_command(id, params)` — Execute a command
- `get_scheduled_tasks()` — Define scheduled tasks
- `get_background_workers()` — Define background workers
- `get_health_status()` — Report host health
- `collect_inventory()` — Collect system inventory
- `collect_performance_counters()` — Collect metrics
- `collect_files(paths)` — Collect files from host
- `collect_events(source, since)` — Collect event logs
- `execute_playbook_action(id, context)` — Run playbook actions
- `execute_automation_action(id, context)` — Run automation actions

## Extension Points

| Extension Point | Target | Description |
|----------------|--------|-------------|
| Dashboard Widget | Server | Add widgets to the dashboard |
| REST API Route | Server | Add API endpoints |
| Navigation Item | Server | Add sidebar navigation |
| Settings Panel | Server | Add settings UI |
| Provider | Server | Offer a provider implementation |
| Notification Channel | Server | Send notifications |
| Background Job | Server | Run scheduled background tasks |
| Database Model | Server | Add ORM models and migrations |
| Command | Agent | Register executable commands |
| Scheduled Task | Agent | Define cron-based tasks |
| Background Worker | Agent | Long-running background processes |
| Health Check | Agent | Report host health |
| Inventory Collector | Agent | Collect system information |
| Performance Counter | Agent | Collect performance metrics |
| File Collector | Agent | Collect files from hosts |
| Event Collector | Agent | Collect event logs |
| Playbook Action | Hybrid | Execute automation actions |

## Public Interfaces

Plugins may use:
- All methods and properties defined in their SDK base class
- The `PluginMessageBus` for communication
- The `PluginTokenManager` for authentication
- The `PluginLoader` for discovery (read-only)

## Private Interfaces

Plugins must NOT use:
- Internal database session management
- Other plugins' internal state
- Server-internal middleware or decorators
- Non-SDK ORM models directly
- Any `_*` prefixed methods or attributes

## Versioning

The SDK follows semantic versioning:
- **Major**: Breaking changes to public interfaces
- **Minor**: New extension points or capabilities
- **Patch**: Bug fixes and improvements

Current SDK version: `3.0.0`
