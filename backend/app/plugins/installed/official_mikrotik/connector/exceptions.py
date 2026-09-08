"""Exceptions for switch connectors.

Names do not shadow Python builtins; the legacy aliases at the bottom keep
backwards compatibility for code that imported the old names.
"""


class SwitchConnectorError(Exception):
    """Base exception for switch connector errors."""


class ConnectorConnectionError(SwitchConnectorError):
    """Raised when establishing a connection to a switch fails."""


class ConnectorAuthenticationError(ConnectorConnectionError):
    """Raised when authentication against a switch fails."""


class ConnectorCommandError(SwitchConnectorError):
    """Raised when command execution on a switch fails."""


# Backwards-compatible aliases (legacy import names).
ConnectionError = ConnectorConnectionError
CommandError = ConnectorCommandError
