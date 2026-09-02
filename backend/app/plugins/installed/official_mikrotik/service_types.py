"""Shared value types for the MikroTik plugin."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CommandResult:
    success: bool
    output: str = ""
    error: str = ""
    duration_ms: int = 0
