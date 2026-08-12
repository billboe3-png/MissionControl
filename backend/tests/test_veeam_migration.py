"""Tests for the Veeam live-registry Alembic migration."""

import pytest


def test_migration_revision_chains_from_head():
    from pathlib import Path
    import re

    path = (
        Path(__file__).parent.parent
        / "alembic"
        / "versions"
        / "f1a2b3c4d5e6_veeam_live_registry.py"
    )
    raw = path.read_text(encoding="utf-8")
    assert re.search(r'^revision: str = "f1a2b3c4d5e6"', raw, re.M)
    assert re.search(r'^down_revision: .* = "6b29cb7f19c9"', raw, re.M)
    assert "add_column" in raw
    assert "backfill" in raw.lower()
    assert "drop_column" in raw


def test_migration_upgrade_backfills_from_integration_profiles():
    from pathlib import Path
    import re

    path = (
        Path(__file__).parent.parent
        / "alembic"
        / "versions"
        / "f1a2b3c4d5e6_veeam_live_registry.py"
    )
    raw = path.read_text(encoding="utf-8")
    assert "integration_profiles" in raw
    assert "integration_type = 'veeam'" in raw
