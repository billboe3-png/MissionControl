# Changelog

All notable changes to Mission Control Community Edition.

## [1.0.0-rc1] — 2026-07-27

### Added
- Plugin framework with ServerPluginSDK lifecycle (setup/start/stop)
- Plugin loader with auto-discovery from `plugins/installed/*/plugin.json`
- Plugin registry with async route registration
- Event Bus system with typed events for all integrations
- Dashboard Aggregator pattern delegating to domain services

#### Official Plugins
- Zabbix monitoring plugin (full JSON-RPC provider, dashboards, alerts)
- Veeam backup plugin (jobs, sessions, repositories, alerts)
- UniFi Site Manager plugin (controllers, sites, devices, clients, alerts, wireless)
- Docker & Container Monitoring plugin (hosts, containers, images, volumes, networks, compose stacks)

#### AI Operations Assistant
- Natural language query endpoint (`/api/v1/ai/query`)
- AI dashboard cards endpoint (`/api/v1/ai/dashboard-cards`)
- Context builder aggregating data from all sources
- Prompt library with 11 reusable templates
- Incident summarizer with root cause analysis
- Correlation engine with cascading failure detection
- Recommendation engine with confidence scoring
- 8 AI providers: Ollama, OpenAI, Azure OpenAI, Anthropic, Local LLM, LM Studio, OpenRouter, Rule-Based

#### Plugin Marketplace
- Multi-repository support (official, community, private enterprise)
- Secure installation workflow: download → verify → extract → register → enable
- Plugin signature verification (SHA256, Ed25519, RSA)
- Compatibility engine (SDK, Python, edition, platform, database, agent)
- Dependency resolution with circular dependency prevention
- Plugin update and rollback support
- Marketplace health dashboard
- 15 REST API endpoints for marketplace operations

#### RC1 Stabilization
- API consistency audit framework
- Plugin integration validation
- Security validation (JWT, RBAC, secrets, rate limiting, CORS)
- Performance benchmarking with targets (dashboard <500ms, heartbeat <100ms)
- RC1 certification report generator (Markdown, JSON, summary text)
- CLI validation script (`scripts/validate_rc1.py`)

### Infrastructure
- PostgreSQL 16 with SQLAlchemy ORM
- Redis for caching and event queuing
- FastAPI with async endpoints
- Docker Compose production stack
- Alembic migration framework with 5 chain tips
- Rate limiting middleware (sliding window)
- Structured logging with request context
- Fernet encryption for credentials at rest

## [0.9.0] — 2026-07-01

### Added
- Initial platform architecture
- Agent fleet management
- Task and project management
- Notes and documentation
- Identity and authentication
- Integration framework
- Setup wizard
- Remote access
- Sites management
- Automation engine
