# Contributing to Mission Control

Thank you for your interest in contributing to Mission Control Community Edition.

## Getting Started

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest backend/tests/`
5. Run linter: `ruff check backend/`
6. Submit a pull request

## Development Setup

```bash
# Clone
git clone https://github.com/your-org/mission-control.git
cd mission-control

# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run dev

# Docker
docker compose up -d
```

## Code Standards

- Python 3.12+
- Type hints required on all functions
- Docstrings on all public classes and methods
- ruff: 0 errors before commit
- pytest: all tests pass
- No secrets in code — use environment variables
- Follow existing code patterns

## Plugin Development

Plugins use the `ServerPluginSDK` base class:

```python
from app.plugins.server import ServerPluginSDK

class MyPlugin(ServerPluginSDK):
    @property
    def name(self) -> str:
        return "My Plugin"

    async def setup(self) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    def get_dashboard_widgets(self) -> list[dict]: ...
    def get_routes(self): ...
    def get_navigation(self) -> list[dict]: ...
```

Place plugins in `backend/app/plugins/installed/<your-plugin>/` with a `plugin.json`.

## Reporting Issues

- Use GitHub Issues
- Include steps to reproduce
- Include environment details
- Attach logs if available

## License

By contributing, you agree that your contributions will be licensed under the project license.
