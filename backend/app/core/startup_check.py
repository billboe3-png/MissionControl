"""
Mission Control Startup Configuration Check

Validates required environment variables before FastAPI starts.
Provides human-friendly error messages instead of Pydantic tracebacks.
"""

import os
import sys

_BANNER = """
============================================================
  Mission Control Startup Error
============================================================

  {message}

  {instruction}

============================================================
"""


def _fail(message: str, instruction: str) -> None:
    """Print a friendly error and exit."""
    print(
        _BANNER.format(message=message, instruction=instruction),
        file=sys.stderr,
    )
    sys.exit(1)


def validate_secret_key() -> str:
    """
    Validate MISSIONCONTROL_SECRET_KEY is present and valid.

    Returns the key string if valid, otherwise exits with code 1.
    """
    key = os.environ.get("MISSIONCONTROL_SECRET_KEY", "").strip()

    if not key:
        _fail(
            message="MISSIONCONTROL_SECRET_KEY is missing.",
            instruction=(
                "Generate one using:\n"
                "\n"
                "  python -c \"from cryptography.fernet import Fernet; "
                'print(Fernet.generate_key().decode())"\n'
                "\n"
                "Add it to your .env file and restart Docker."
            ),
        )

    try:
        from cryptography.fernet import Fernet, InvalidToken

        Fernet(key.encode() if isinstance(key, str) else key)
    except (InvalidToken, ValueError):
        _fail(
            message="MISSIONCONTROL_SECRET_KEY is not a valid Fernet key.",
            instruction=(
                "Generate a new key using:\n"
                "\n"
                "  python -c \"from cryptography.fernet import Fernet; "
                'print(Fernet.generate_key().decode())"\n'
                "\n"
                "Replace the value in your .env file and restart Docker."
            ),
        )

    return key


def validate_all() -> dict[str, str]:
    """
    Run all startup validations.

    Returns a dict of validated values on success.
    """
    return {"secret_key": validate_secret_key()}
