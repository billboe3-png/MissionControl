# Coding Standards

Mission Control enforces consistent code style across the backend and frontend. Follow these standards in every pull request.

## Backend — Python

### Linter: Ruff

Ruff is configured in `backend/pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
extend-ignore = ["E501", "B008"]
```

**Enabled rule sets:**

| Code | Meaning |
|------|---------|
| `E` | pycodestyle errors |
| `F` | Pyflakes |
| `I` | isort (import sorting) |
| `UP` | pyupgrade (modern Python syntax) |
| `B` | flake8-bugbear |

**Ignored rules:**

- `E501` — line length (handled by formatter)
- `B008` — function calls in default arguments (FastAPI `Depends()` pattern)

Run the linter before every commit:

```bash
cd backend
ruff check app/ tests/
```

Auto-fix safe issues:

```bash
ruff check --fix app/ tests/
```

### Formatting

Use `ruff format` for consistent formatting:

```bash
ruff format app/ tests/
```

The formatter targets 88-character lines (Black-compatible).

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Modules | `snake_case` | `remote_service.py` |
| Classes | `PascalCase` | `RemoteService` |
| Functions | `snake_case` | `get_host_by_id()` |
| Variables | `snake_case` | `host_count` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| Private members | `_leading_underscore` | `_encrypt_value()` |
| Boolean variables | `is_`/`has_` prefix | `is_active`, `has_credentials` |

### Import Ordering

Imports follow this order (enforced by ruff `I` rules):

1. Standard library
2. Third-party packages
3. First-party (`app.*`)

Each group is separated by a blank line. Within each group, imports are sorted alphabetically.

```python
import logging
import os
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db.database import get_db
from app.models.db.host import RemoteHost
from app.schemas.remote import HostCreate
from app.services.remote_service import RemoteService
```

### Type Hints

All function signatures must include type hints:

```python
def get_host_by_id(db: Session, host_id: int) -> RemoteHost | None:
    ...

async def execute_command(
    host_id: int,
    command: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommandResult:
    ...
```

Use `X | None` instead of `Optional[X]` (Python 3.12 syntax).

### Docstrings

Use Google-style docstrings for public functions and classes:

```python
def encrypt_credential(plaintext: str, secret_key: str) -> str:
    """Encrypt a credential value using Fernet symmetric encryption.

    Args:
        plaintext: The raw credential string to encrypt.
        secret_key: The Fernet key used for encryption.

    Returns:
        The base64-encoded encrypted value.
    """
    ...
```

Docstrings are not required for obvious one-liners or private helpers. Do not add docstrings solely to satisfy a linter.

### Error Handling

Return HTTP exceptions from routers, never from services:

```python
# In the router
@router.get("/hosts/{host_id}")
def read_host(
    host_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HostResponse:
    host = RemoteService.get_host(db, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return host
```

Services raise domain exceptions or return `None`. Routers translate them to HTTP status codes.

### Logging

Use the standard library logger with `__name__`:

```python
import logging

logger = logging.getLogger(__name__)
```

Log at appropriate levels: `logger.info()` for normal operations, `logger.warning()` for recoverable issues, `logger.error()` for failures.

## Frontend — TypeScript

### Type Checking

TypeScript is configured in strict mode (`tsconfig.app.json`):

```json
{
  "compilerOptions": {
    "strict": true,
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "react-jsx",
    "noEmit": true,
    "isolatedModules": true
  }
}
```

Run the type checker before every commit:

```bash
cd frontend
npx tsc --noEmit
```

### Linting

ESLint is configured with React hooks and refresh plugins:

```bash
cd frontend
npm run lint
```

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Components | `PascalCase` | `DataTable.tsx` |
| Pages | `PascalCase` | `Dashboard.tsx` |
| Hooks | `use` prefix, `camelCase` | `useHosts.ts` |
| Contexts | `PascalCase` + `Context` | `ToastContext.ts` |
| Services | `camelCase` | `apiClient.ts` |
| Types/Interfaces | `PascalCase` | `RemoteHost` |
| CSS classes | `kebab-case` | `page-header` |
| Constants | `UPPER_SNAKE_CASE` | `API_BASE_URL` |

### Component Patterns

Use functional components with explicit prop types:

```tsx
interface HostCardProps {
  host: RemoteHost;
  onEdit: (id: number) => void;
  onDelete: (id: number) => void;
}

export function HostCard({ host, onEdit, onDelete }: HostCardProps) {
  return (
    <div className="host-card">
      <h3>{host.name}</h3>
      <button onClick={() => onEdit(host.id)}>Edit</button>
    </div>
  );
}
```

### File Organization

Each page lives in its own directory under `src/pages/<domain>/`:

```
src/pages/remote/
├── Hosts.tsx
├── Credentials.tsx
├── Execute.tsx
├── History.tsx
└── Files.tsx
```

Shared components go in `src/components/common/`. Domain-specific components go in `src/components/<domain>/`.

## General Rules

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add bulk command execution endpoint
fix: resolve null pointer in credential decryption
refactor: extract rate limiting into middleware
docs: update database migration guide
test: add integration tests for playbook execution
ci: add ruff lint step to GitHub Actions
```

### Code Comments

Do not add comments unless the logic is non-obvious. Code should be self-documenting through clear naming and structure. Comments that restate what the code does are noise.

### Dead Code

Remove dead code immediately. Do not comment it out. Version control preserves history.

### File Length

Keep files under 400 lines. If a file exceeds this, consider splitting it into focused modules.

## Cross-References

- Backend lint config: `backend/pyproject.toml`
- Frontend lint config: `frontend/package.json` (eslint)
- TypeScript config: `frontend/tsconfig.app.json`
- See [BACKEND.md](BACKEND.md) for architecture patterns.
- See [FRONTEND.md](FRONTEND.md) for component patterns.
- See [TESTING.md](TESTING.md) for test conventions.
