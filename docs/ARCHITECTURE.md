# Architecture

Mission Control follows a Modular Monolith architecture.

## Backend Architecture

- **FastAPI** - Python web framework for the backend API
- **React + TypeScript** - Frontend dashboard
- **PostgreSQL** - Primary database
- **Redis** - Cache layer
- **Nginx** - Reverse proxy

## CLI Architecture

The Mission Control CLI follows a modular PowerShell-based architecture:

```
mc.ps1
    ↓
Bootstrap
    ↓
Registry
    ↓
Command
    ↓
Libraries
    ↓
Output
```

### Component Responsibilities

#### Bootstrap (`scripts/lib/Bootstrap.ps1`)

- Parses raw CLI arguments into structured data
- Separates global options from command arguments
- Creates execution context with project root, command path, and options
- Loads and merges configuration from files and command-line options
- Dispatches commands to registered handlers via the registry

#### Registry (`scripts/lib/Registry.ps1`)

- Maintains the command registry with metadata for all CLI commands
- Registers commands with their handler functions, descriptions, usage, and examples
- Retrieves command handlers by name for dispatch
- Provides command metadata for help system and documentation
- Ensures commands are discoverable and self-documenting

#### Config (`scripts/lib/Config.ps1`)

- Loads configuration from JSON files
- Merges configuration from multiple sources (file, command-line, defaults)
- Provides configuration values to commands through the context
- Handles configuration file validation and error handling

#### Validation (`scripts/lib/Validation.ps1`)

- Provides reusable validation helpers for commands
- Validates argument counts and throws descriptive errors
- Validates subcommands against allowed values
- Checks for required executables (git, docker, etc.)
- Validates repository state for git operations

#### Logger (`scripts/lib/Logger.ps1`)

- Initializes logging for command execution
- Writes timestamped log entries to files
- Supports multiple log levels (INFO, WARN, ERROR, DEBUG, SUCCESS)
- Handles log file creation and directory management
- Provides conditional console output based on verbosity settings

#### Output (`scripts/lib/Output.ps1`)

- Central output rendering engine for all commands
- Renders results in multiple formats (console, JSON, JSON-pretty)
- Dispatches to specific renderers based on result type
- Handles colorization and formatting for console output
- Ensures consistent output across all commands

#### Commands (`scripts/commands/`)

Each command module is responsible for:
- Registering itself with the command registry
- Implementing its specific business logic
- Returning structured result objects (PSCustomObject with Type property)
- Using shared libraries for validation, logging, and output
- Never writing directly to console (uses Output.ps1 instead)

Key commands:
- **Help** - Generates and displays command help from registry metadata
- **Doctor** - Performs environment, Docker, and HTTP health checks
- **Docker** - Manages Docker Compose stack (up, down, logs)
- **Git** - Provides safe wrappers for Git operations (status, commit)
- **Status** - Displays local developer environment status
- **Version** - Shows CLI version information
- **Init** - Performs idempotent project initialization
