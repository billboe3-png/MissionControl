# Contributing to Mission Control

Thank you for your interest in contributing to Mission Control!

## Branching Strategy

Mission Control uses a simple branching model:

- **main** - Production-ready code
- **develop** - Integration branch for features
- **feature/*** - Feature branches (e.g., `feature/docker-integration`)

Create a feature branch from `develop` for your work:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

## Commit Style

Use conventional commit prefixes to make commit history readable:

- **feat:** - New feature
- **fix:** - Bug fix
- **refactor:** - Code refactoring without behavior change
- **docs:** - Documentation changes
- **test:** - Test additions or changes
- **ci:** - CI/CD configuration changes

### Examples

```bash
git commit -m "feat: add docker compose up command"
git commit -m "fix: resolve doctor null message issue"
git commit -m "refactor: simplify validation helper"
git commit -m "docs: update README with quick start guide"
git commit -m "test: add validation tests for subcommands"
git commit -m "ci: add GitHub Actions workflow"
```

## Before Opening a Pull Request

Before creating a pull request, ensure you have:

1. **Run tests locally**
   ```powershell
   Invoke-Pester
   ```

2. **Run the quality gate**
   ```powershell
   ./scripts/Invoke-Quality.ps1
   ```

   This is the same check that CI runs on every push and pull request.

3. **Update documentation** if your changes affect user-facing behavior

4. **Ensure your branch is up to date**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout feature/your-feature-name
   git rebase develop
   ```

## Coding Standards

### Keep Changes Small

- One feature per sprint
- Small, focused pull requests are easier to review
- Break large changes into smaller, logical pieces

### Avoid Duplication

- Reuse shared libraries in `scripts/lib/`
- Check if a helper function already exists before creating a new one
- Follow existing patterns for similar functionality

### Command Implementation

- Commands should return `PSCustomObject` with a `Type` property
- Output only through `Output.ps1` - never use `Write-Host` directly in commands
- Use the command registry for metadata (description, usage, examples)
- Follow the existing command structure in `scripts/commands/`

### Validation

- Use validation helpers from `Validation.ps1` (e.g., `Assert-McArgumentCount`, `Assert-McValidSubcommand`)
- Provide clear error messages with usage information
- Validate inputs early in the command execution

### Logging

- Use `Write-McLog` from `Logger.ps1` for logging
- Log at appropriate levels (INFO, WARN, ERROR, DEBUG, SUCCESS)
- Never write directly to log files

## Pull Request Checklist

Before submitting your pull request, verify:

- [ ] Tests pass locally (`Invoke-Pester`)
- [ ] Quality gate passes (`./scripts/Invoke-Quality.ps1`)
- [ ] Documentation updated (README.md, command help, or architecture docs)
- [ ] No duplicate code - reused existing libraries where possible
- [ ] No breaking changes to existing commands or public APIs
- [ ] CI passes on your pull request
- [ ] Commit messages follow the commit style guide
- [ ] Branch is based on `develop` and is up to date

## Pull Request Process

1. Create a feature branch from `develop`
2. Make your changes following the coding standards
3. Run tests and quality gate locally
4. Update documentation as needed
5. Push your branch to the repository
6. Open a pull request targeting `develop`
7. Address review feedback
8. Once approved, merge to `develop`

## Getting Help

If you need help with contribution:

- Check the [README.md](README.md) for project overview
- See [docs/architecture.md](docs/architecture.md) for architecture details
- Run `./scripts/mc.ps1 help <command>` for command-specific help
- Review existing command implementations in `scripts/commands/`

## Code of Conduct

Be respectful and constructive in all interactions. Focus on what is best for the community and the project.
