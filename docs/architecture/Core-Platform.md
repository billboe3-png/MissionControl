# Core Platform Definition

This document defines what belongs inside the Mission Control core. The core provides frameworks, not features. Vendor-specific functionality must never be added directly to the core.

## Core Components

### Authentication & Authorization
- JWT-based authentication with role-based access control
- User management (create, update, delete, roles)
- Session management with token refresh
- API key management for service-to-service auth
- Agent token management for agent registration

### Multi-Tenancy
- Company (tenant) management with resource isolation
- Site management within companies
- Resource scoping (agents, integrations, tasks per company/site)
- Tenant-aware database queries

### Dashboard Framework
- Widget registration and rendering system
- Data provider interface for widgets
- Dashboard layout and configuration
- Real-time data refresh

### Navigation Framework
- Sidebar navigation with collapsible groups
- Breadcrumb navigation
- Route registration and label mapping
- Plugin-contributed navigation items

### Settings Framework
- Global application settings
- Per-user preferences
- Plugin settings panels
- Environment configuration

### Plugin Manager
- Plugin registration and lifecycle management (register, enable, disable, start, stop)
- Plugin discovery and loading
- Plugin configuration storage
- Plugin health monitoring
- Plugin marketplace integration

### Plugin SDK
- Base classes for server, agent, and hybrid plugins
- Extension points for dashboard, API, navigation, settings
- Communication protocol for server↔agent messaging
- Token management for plugin authentication

### Automation Engine
- Playbook definition and execution
- Step execution with variable substitution
- Approval workflows
- Schedule-based and event-triggered execution
- Execution logging and audit trail

### Scheduler
- Cron-based task scheduling
- Playbook schedule management
- Scheduled command execution
- Background job management

### Notification Engine
- Pluggable notification channels (email, Slack, Teams, webhooks)
- Notification templates
- Alert severity levels
- Notification history

### AI Engine
- Chat interface and conversation management
- Provider abstraction (OpenAI, Anthropic, mock)
- Context management for conversations
- Tool use and function calling framework

### Agent Manager
- Agent registration and heartbeat tracking
- Command dispatch and result collection
- Agent inventory management
- Agent health monitoring
- Registration token management

### REST API
- FastAPI application with OpenAPI documentation
- Router registration framework
- Request/response validation (Pydantic)
- Rate limiting middleware
- CORS configuration
- Security headers

### Database
- SQLAlchemy ORM with PostgreSQL
- Alembic migration framework
- Session management with dependency injection
- Redis caching layer

### Logging
- Structured logging with request IDs
- Request/response timing
- Error logging with context
- Plugin-specific log namespacing

### Health Checks
- Liveness probe (`/health/live`)
- Readiness probe (`/health/ready`) with dependency checks
- Per-service health status

### Metrics
- Request rate and latency metrics
- Plugin health metrics
- Agent connectivity metrics
- System resource metrics

### Audit
- Operation audit trail
- User action logging
- Plugin operation logging
- Compliance event recording

### Configuration
- Environment-based configuration
- Pydantic settings with validation
- Computed properties (database URL, Redis URL)
- Rate limit configuration

## What Does NOT Belong in Core

The following must always be implemented as plugins:

- Vendor-specific monitoring (Zabbix, Grafana, Prometheus)
- Cloud provider integration (Azure, AWS, GCP)
- Identity provider integration (AD, Entra ID, Okta)
- Virtualization management (Hyper-V, Proxmox, VMware)
- Container management (Docker, Kubernetes)
- Remote desktop tools (TeamViewer, RustDesk)
- Backup management (Veeam, Nakivo)
- Database management (SQL Server, MySQL, MongoDB)
- ITSM integration (Jira, ServiceNow)
- Communication channels (Slack, Teams, Email)

## The Core Should Remain Lightweight

The Mission Control core is a framework. It provides:
- Authentication and authorization
- Navigation and dashboard structure
- Database and caching
- Plugin management
- Automation execution
- API infrastructure

It does NOT provide:
- Vendor-specific monitoring dashboards
- Cloud management interfaces
- Identity provider connectors
- Virtualization management
- Any vendor-specific functionality

Every vendor-specific feature is a plugin that uses the SDK.
