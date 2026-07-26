# Contributing to Mission Control

Thank you for your interest in contributing to Mission Control! This guide covers everything you need to get started.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Commit Messages](#commit-messages)
- [Code Review](#code-review)
- [Contributor License Agreement](#contributor-license-agreement)
- [Release Process](#release-process)

---

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to its terms. Report unacceptable behavior to [conduct@missioncontrol.dev](mailto:conduct@missioncontrol.dev).

---

## Ways to Contribute

### Report Bugs

1. Search [existing issues](https://github.com/billboe3-png/MissionControl/issues) first.
2. Open a new issue using the **Bug Report** template.
3. Include reproduction steps, expected behavior, actual behavior, and environment details.

### Request Features

Open an issue using the **Feature Request** template. Describe the problem you are trying to solve, your proposed solution, and alternatives you considered.

### Submit Code

Pick an issue labeled `good first issue` or `help wanted`, or propose your own improvement via a new issue first.

### Improve Documentation

Documentation PRs are always welcome. Fixes for typos, clarifications, and new guides are all valuable. See the [docs/](docs/) directory.

### Write Plugins

Build and share plugins for the community marketplace. See [docs/PLUGINS.md](docs/PLUGINS.md) for the plugin SDK reference.

### Report Security Vulnerabilities

**Do not open public issues for security vulnerabilities.** Follow the process in [SECURITY.md](SECURITY.md).

---

## Development Setup

### Prerequisites

- Python 3.12
- Node.js 20+ and npm 10+
- PostgreSQL 16
- Redis 7
- Git

### Backend

```bash
git clone https://github.com/billboe3-png/MissionControl.git
cd MissionControl
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Database

```bash
cp .env.example .env
# Edit .env with your database and Redis credentials
alembic upgrade head
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend
pytest tests/ -v

# Frontend
cd frontend && npm run test

# Linting
ruff check app/
cd frontend && npm run lint

# Type checking
mypy app/
cd frontend && npm run typecheck
```

### Pre-commit Hooks

We use pre-commit to run linters and formatters automatically:

```bash
pip install pre-commit
pre-commit install
```

---

## Coding Standards

### Python (Backend)

- **Formatter**: Ruff (line length 88)
- **Linter**: Ruff with default rules
- **Type checking**: mypy with strict mode
- **Style**: Follow [PEP 8](https://peps.python.org/pep-0008/) as enforced by Ruff
- All new code must include type annotations
- All new functions and classes must include docstrings
- Tests are required for new features and bug fixes

### TypeScript / React (Frontend)

- **Formatter**: Prettier (default config)
- **Linter**: ESLint (project config)
- **Style**: Functional components with hooks only — no class components
- Use TypeScript strict mode — no `any` types
- Prefer named exports over default exports
- Co-locate component tests with component files

### General

- Keep functions small and focused — single responsibility
- Prefer composition over inheritance
- Use meaningful names — no abbreviations in public APIs
- Handle errors explicitly; never swallow exceptions silently
- Write commit messages that explain **why**, not just **what**

---

## Pull Request Process

1. **Open an issue first** for non-trivial changes so the approach can be discussed.
2. **Fork** the repository and create a branch from `main`:
   ```bash
   git checkout -b feature/my-feature
   ```
3. **Make your changes** following the coding standards above.
4. **Write or update tests** to cover your changes.
5. **Run the full test suite** and linters before submitting:
   ```bash
   pytest tests/ -v
   ruff check app/
   mypy app/
   cd frontend && npm run lint && npm run typecheck && npm run test
   ```
6. **Push** your branch and open a Pull Request against `main`.
7. **Fill out the PR template** — describe what changed, why, and how to test.
8. **Respond to review feedback** promptly. Push additional commits to your branch as needed.

A maintainer will review your PR and may request changes. Once approved and CI passes, a maintainer will merge the PR.

---

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style change (no logic change) |
| `refactor` | Code restructuring (no feature or fix) |
| `test` | Adding or updating tests |
| `chore` | Build, CI, dependency, or tooling change |
| `perf` | Performance improvement |

### Scope

Use the affected component: `api`, `agent`, `frontend`, `db`, `plugin-sdk`, `ci`, `docs`.

### Examples

```
feat(agent): add heartbeat jitter to reduce thundering herd

fix(api): return 404 for deleted agent instead of 500

docs: update deployment guide for Docker Compose v2

chore(ci): pin GitHub Actions runners to ubuntu-22.04
```

### Rules

- Subject line max 72 characters
- Use imperative mood in the subject ("add feature", not "added feature")
- Reference related issues with `Closes #123` or `Refs #123` in the footer

---

## Code Review

All PRs require at least one approving review from a maintainer before merge.

### What reviewers look for

- Correctness and completeness of the change
- Test coverage for new or modified behavior
- Adherence to coding standards
- No regressions in existing functionality
- Clear, readable code and commit messages
- Security implications (no secrets, no injection vectors)

### Etiquette

- Be constructive and specific in feedback
- Suggest alternatives rather than just pointing out problems
- Approve promptly when the PR is ready — do not block without good reason
- Authors should respond to every comment, even if just to acknowledge

---

## Contributor License Agreement

Contributions to Mission Control Community Edition are made under the project license (AGPL-3.0). By submitting a Pull Request, you agree that your contribution is licensed under the same terms.

For Enterprise Edition contributions, a separate Contributor License Agreement (CLA) may be required. If applicable, a maintainer will request you sign the CLA before your PR can be merged.

---

## Release Process

Mission Control follows [Semantic Versioning](https://semver.org/):

- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backward-compatible
- **Patch** (0.0.X): Bug fixes, backward-compatible

### Steps

1. Maintainers update [CHANGELOG.md](CHANGELOG.md) with all changes for the release.
2. A release branch is created (`release/vX.Y.Z`) and tagged.
3. CI runs the full test suite and builds release artifacts.
4. The release is published to GitHub Releases with release notes.
5. Docker images are pushed to the container registry.

### Release Cadence

- **Patch releases**: As needed for bug fixes
- **Minor releases**: Approximately monthly
- **Major releases**: Annually, with a beta period

---

## Questions?

- Open a [Discussion](https://github.com/billboe3-png/MissionControl/discussions) for general questions
- See the [Documentation Hub](docs/) for guides and references
- Reach out on the community Slack (link in the repository About section)

Thank you for contributing to Mission Control!
