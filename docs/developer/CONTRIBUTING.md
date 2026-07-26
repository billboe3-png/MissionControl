# Contributing to Mission Control

Thank you for your interest in contributing to Mission Control. This guide covers everything you need to know to submit a high-quality contribution.

## Getting Started

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:

```bash
git clone https://github.com/<your-username>/MissionControl.git
cd MissionControl
```

3. **Set up the development environment** by following [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md).
4. **Read the coding standards** in [CODING_STANDARDS.md](CODING_STANDARDS.md).

## Branching Strategy

Mission Control uses a two-tier branching model:

```
main ─────────────────────── production-ready
  └── develop ────────────── integration branch
        └── feature/* ────── work branches
        └── fix/* ────────── bug fix branches
        └── hotfix/* ─────── urgent production fixes
```

### Branch Types

| Branch | Prefix | Example | Target |
|--------|--------|---------|--------|
| Feature | `feature/` | `feature/bulk-execution` | `develop` |
| Bug fix | `fix/` | `fix/credential-decryption` | `develop` |
| Hotfix | `hotfix/` | `hotfix/auth-bypass` | `main` + `develop` |
| Documentation | `docs/` | `docs/api-reference` | `develop` |

### Creating a Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

## Making Changes

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>
```

| Type | When to Use | Example |
|------|-------------|---------|
| `feat:` | New feature | `feat: add bulk command execution` |
| `fix:` | Bug fix | `fix: resolve null credential decryption` |
| `refactor:` | Code restructure (no behavior change) | `refactor: extract rate limiter middleware` |
| `docs:` | Documentation only | `docs: update migration guide` |
| `test:` | Adding or updating tests | `test: add webhook repository tests` |
| `ci:` | CI/CD changes | `ci: add ruff lint step` |
| `chore:` | Maintenance tasks | `chore: update dependencies` |

**Good commit messages:**

```bash
git commit -m "feat: add webhook endpoint for external integrations"
git commit -m "fix: prevent SQL injection in host search parameter"
git commit -m "refactor: simplify credential encryption flow"
git commit -m "test: add integration tests for playbook execution"
```

**Bad commit messages:**

```bash
git commit -m "fix stuff"
git commit -m "WIP"
git commit -m "updates"
```

### Keep Changes Focused

- One feature or fix per pull request.
- Small, focused PRs are easier to review and merge.
- Break large changes into a series of smaller PRs.

## Before Opening a Pull Request

### 1. Sync with upstream

```bash
git checkout develop
git pull origin develop
git checkout feature/your-feature-name
git rebase develop
```

### 2. Run the quality gate

```bash
# Backend lint
cd backend
ruff check app/ tests/

# Backend format check
ruff format --check app/ tests/

# Frontend type check
cd frontend
npx tsc --noEmit

# Backend tests
cd backend
python -m pytest tests/ -v
```

### 3. Update documentation

If your changes affect:
- API endpoints → update [API.md](API.md)
- Database models → update [DATABASE.md](DATABASE.md)
- Development setup → update [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md)
- Architecture → update the relevant architecture doc

### 4. Verify your branch is clean

```bash
git status
```

Remove any debug code, print statements, or temporary files.

## Pull Request Process

### 1. Push your branch

```bash
git push origin feature/your-feature-name
```

### 2. Create the PR on GitHub

- **Title**: Use the same Conventional Commits format as your commits.
- **Description**: Explain what the PR does, why, and any relevant context.
- **Target**: `develop` (not `main`).

### PR Description Template

```markdown
## What

Brief description of the change.

## Why

Motivation or problem being solved.

## How

Implementation approach (if non-obvious).

## Testing

How was this tested?

- [ ] Backend tests pass (`python -m pytest tests/ -v`)
- [ ] Frontend type checks (`npx tsc --noEmit`)
- [ ] Ruff lint passes (`ruff check app/ tests/`)
- [ ] Manual testing performed (describe below)

## Screenshots

If applicable, add screenshots or recordings.
```

### 3. Address review feedback

- Respond to all review comments.
- Make requested changes in new commits (do not force-push during review).
- Re-request review when ready.

### 4. Merge

Once approved, the PR is merged to `develop` using the GitHub merge button (squash merge preferred for clean history).

## Pull Request Checklist

Before requesting review, verify:

- [ ] Backend lint passes: `ruff check app/ tests/`
- [ ] Frontend type check passes: `npx tsc --noEmit`
- [ ] Backend tests pass: `python -m pytest tests/ -v`
- [ ] Documentation updated (if applicable)
- [ ] No secrets or credentials in the diff
- [ ] No breaking changes to existing APIs (or documented in PR description)
- [ ] Commit messages follow Conventional Commits
- [ ] Branch is based on and targeting `develop`

## Code Review Guidelines

### As a Reviewer

- Be constructive and specific in feedback.
- Focus on correctness, security, and maintainability.
- Approve when the code meets the project standards.
- Use "Request Changes" for blocking issues, "Comment" for suggestions.

### As an Author

- Respond to every comment, even if just to acknowledge.
- Do not take feedback personally — the goal is a better codebase.
- If you disagree, explain your reasoning and propose alternatives.

## Reporting Issues

### Bug Reports

Include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (OS, Python version, Node version)
- Relevant logs or screenshots

### Feature Requests

Include:
- Problem statement (what pain point does this solve?)
- Proposed solution
- Alternatives considered
- Impact on existing functionality

## Code of Conduct

Be respectful and constructive in all interactions. Focus on what is best for the project and its users.

## Getting Help

- Read the [Developer Guide](DEVELOPER_GUIDE.md) for navigation.
- Check [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) for environment issues.
- Open a discussion on GitHub for questions.
- Review existing code for patterns and conventions.

## Cross-References

- See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for the full documentation index.
- See [CODING_STANDARDS.md](CODING_STANDARDS.md) for code style rules.
- See [CI_CD.md](CI_CD.md) for how your PR will be validated.
- See [RELEASE_PROCESS.md](RELEASE_PROCESS.md) for how releases work.
