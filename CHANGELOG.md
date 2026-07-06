# Changelog

All notable changes to Mission Control will be documented in this file.

## [0.1.0] - Development Preview

### Added

- CLI framework with command registry system
- Bootstrap module for argument parsing and context creation
- Registry module for command registration and dispatch
- Config module for configuration loading and merging
- Validation module with reusable validation helpers
- Logger module for timestamped log entries
- Output engine for console, JSON, and JSON-pretty rendering
- Help command with registry-based documentation
- Doctor command for environment, Docker, and HTTP health checks
- Docker command for Docker Compose stack management (up, down, logs)
- Git command for safe Git operations (status, commit)
- Status command for developer environment status
- Version command for CLI version display
- Init command for idempotent project initialization
- Pester test framework with tests for Bootstrap, Registry, Logger, Helpers, and Validation
- CI quality gate script (Invoke-Quality.ps1)
- GitHub Actions workflow for continuous integration
- VS Code workspace configuration (extensions, settings, tasks, launch)
- Developer documentation (README.md, CONTRIBUTING.md, docs/architecture.md)

### Changed

- Fixed Doctor command null message handling for Git and Python version checks
- Enhanced Help command to display command descriptions from registry metadata
- Added subcommand validation helpers (Assert-McValidSubcommand) to Validation module
- Updated Docker and Git commands to use shared validation helpers

### Fixed

- Doctor command empty Message parameter binding error
- Registry.Tests.ps1 PowerShell version check issue
- Validation.Tests.ps1 Pester 3 syntax compatibility
- Logger.Tests.ps1 directory existence test
- Helpers.Tests.ps1 exit code test for Windows compatibility
