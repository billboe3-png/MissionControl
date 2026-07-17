# Architecture Principles

The foundational principles that guide all architectural decisions in Mission Control.

## Core Principles

### 1. Keep the Core Lightweight

The core platform provides **frameworks, not features**. Authentication, navigation, dashboard layout, automation engine, and plugin management live in the core. All vendor-specific functionality lives in plugins.

**Rule:** If a feature can be delivered as a plugin, it must be delivered as a plugin.

### 2. Vendor Functionality Belongs in Plugins

No vendor-specific code (Proxmox, Zabbix, Azure, etc.) is permitted in the core platform. Every external integration is a plugin that extends the platform through the SDK.

**Rule:** `grep -r "zabbix\|proxmox\|hyperv\|azure\|aws" backend/app/core/` must return zero results (excluding tests and documentation).

### 3. Everything Communicates Through APIs

No direct database access between services. No shared state between processes. All communication happens through the REST API or message bus.

**Rule:** A service never imports from another service's repository directly.

### 4. Agents Execute, Server Orchestrates

The server decides **what** to do. The agent decides **how** to do it. The server never reaches into managed hosts directly when an agent is available.

**Rule:** Server-to-agent commands are declarative (intent), not imperative (shell commands).

### 5. Plugins Use Only the SDK

Plugins interact with the core exclusively through the public SDK interfaces. Private internal APIs are not part of the contract and may change without notice.

**Rule:** If the SDK doesn't expose a capability, extend the SDK — don't bypass it.

### 6. Never Bypass the SDK

When a plugin needs new core functionality, the correct path is to extend the SDK with a new interface, not to access internal modules directly.

**Rule:** Plugins must not import from `app.core.internal`, `app.providers.*`, or any non-SDK module.

### 7. Maintain Backwards Compatibility

Breaking changes require a major version bump. Within a major version, the public API is stable.

**Rule:** Any breaking change to a public interface must be preceded by a deprecation notice of at least two minor versions.

### 8. Security First

Every feature considers authentication, authorization, encryption, and audit logging from the start — not as an afterthought.

**Rule:** No endpoint is added without auth dependency. No credential is stored in plaintext. No operation is executed without audit logging.

### 9. Everything Is Testable

Code that cannot be tested is code that cannot be trusted. If a function is hard to test, the design is wrong.

**Rule:** Every public function has at least one test. Coverage target: 80%+ for core, 70%+ for plugins.

### 10. Everything Is Documented

No public interface exists without documentation. No architectural decision is made without an ADR.

**Rule:** Every SDK interface has a docstring. Every ADR has context, decision, and consequences.

### 11. Everything Is Modular

Components can be replaced without side effects. Plugins can be installed, removed, and upgraded independently.

**Rule:** Removing a plugin does not break the core. Replacing a plugin does not affect other plugins.

## Design Rules

### Separation of Concerns

| Layer | Responsibility |
|-------|---------------|
| Router | HTTP request/response, validation |
| Service | Business logic, orchestration |
| Repository | Data access, queries |
| Provider | External system integration |
| Model | Database schema definition |
| Schema | API request/response models |

### Single Responsibility

Each module, class, and function does one thing. If a function name contains "and", it should be two functions.

### Explicit Over Clever

Readable code beats concise code. Named parameters beat positional arguments. Explicit imports beat wildcard imports.

### Fail Fast, Recover Gracefully

Validate early. Raise errors immediately. Handle errors at the appropriate boundary. Never silently swallow exceptions.

## Anti-Patterns

The following patterns are prohibited in Mission Control:

| Anti-Pattern | Why |
|-------------|-----|
| God class | Violates single responsibility |
| Circular imports | Violates modularity |
| Magic numbers | Violates explicit principle |
| `# type: ignore` | Hides type errors |
| `except: pass` | Swallows errors silently |
| Hardcoded config | Violates twelve-factor app |
| Shared mutable state | Causes race conditions |
| `eval()` / `exec()` | Security vulnerability |
| SQL string concatenation | SQL injection vulnerability |
| Direct DB access from router | Violates separation of concerns |

## Decision Framework

When facing an architectural decision:

1. **Does a relevant ADR exist?** Follow it.
2. **Does the SDK support it?** Use the SDK.
3. **Is it vendor-specific?** It's a plugin.
4. **Is it core functionality?** Consider if it can be a plugin.
5. **Does it affect security?** Consult Security-Standards.md.
6. **Does it change the public API?** Follow API-Standards.md.
7. **None of the above?** Document the decision in Architecture-Decisions.md.
