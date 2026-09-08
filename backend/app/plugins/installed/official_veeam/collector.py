"""
Veeam Hourly Snapshot Collector

Collects Veeam datasets in the background and stores them as
veeam_snapshots rows so the dashboard routes can serve cached data instantly.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.plugins.installed.official_veeam.models import VeeamSnapshot
from app.plugins.installed.official_veeam.provider import VeeamServerProvider

logger = logging.getLogger("plugin.veeam.collector")


def _upsert_snapshot(
    db: Session, server_id: int, dataset: str, payload: dict[str, Any],
) -> None:
    row = db.execute(
        select(VeeamSnapshot).where(
            VeeamSnapshot.server_id == server_id,
            VeeamSnapshot.dataset == dataset,
        )
    ).scalar_one_or_none()

    if row is None:
        db.add(VeeamSnapshot(
            server_id=server_id,
            dataset=dataset,
            payload=json.dumps(payload, default=str),
            collected_at=datetime.now(UTC),
        ))
    else:
        row.payload = json.dumps(payload, default=str)
        row.collected_at = datetime.now(UTC)


async def collect_dataset(
    db: Session,
    provider: VeeamServerProvider,
    server_id: int,
    dataset: str,
    **params: Any,
) -> dict[str, Any]:
    method = _METHODS.get(dataset)
    if method is None:
        raise ValueError(f"Unknown dataset: {dataset}")

    payload = await method(provider, **params)
    _upsert_snapshot(db, server_id, dataset, payload)
    db.commit()
    return payload


async def collect_all(
    db: Session, provider: VeeamServerProvider, server_id: int,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for dataset in _ALL_DATASETS:
        try:
            results[dataset] = await collect_dataset(db, provider, server_id, dataset)
        except Exception as exc:
            logger.error("collect_all server=%s dataset=%s failed: %s", server_id, dataset, exc)
    return results


# ------------------------------------------------------------------ #
# Method mapping                                                     #
# ------------------------------------------------------------------ #

async def _get_summary(provider: VeeamServerProvider, **_: Any) -> dict[str, Any]:
    return await provider.get_summary()


async def _get_jobs(provider: VeeamServerProvider, **_: Any) -> dict[str, Any]:
    return await provider.get_jobs()


async def _get_job_stats(provider: VeeamServerProvider, **_: Any) -> dict[str, Any]:
    return await provider.get_job_stats()


async def _get_job_stats_daily(
    provider: VeeamServerProvider, **params: Any,
) -> dict[str, Any]:
    return await provider.get_job_stats_daily(days=int(params.get("days", 7)))


async def _get_sessions(provider: VeeamServerProvider, **_: Any) -> dict[str, Any]:
    return await provider.get_sessions()


async def _get_session_stats(
    provider: VeeamServerProvider, **_: Any,
) -> dict[str, Any]:
    return await provider.get_session_stats()


async def _get_repositories(
    provider: VeeamServerProvider, **_: Any,
) -> dict[str, Any]:
    return await provider.get_repositories()


async def _get_license(provider: VeeamServerProvider, **_: Any) -> dict[str, Any]:
    return await provider.get_license()


async def _get_capacity_tier(
    provider: VeeamServerProvider, **_: Any,
) -> dict[str, Any]:
    return await provider.get_capacity_tier()


_METHODS: dict[str, Any] = {
    "summary": _get_summary,
    "jobs": _get_jobs,
    "job_stats": _get_job_stats,
    "job_stats_daily": _get_job_stats_daily,
    "sessions": _get_sessions,
    "session_stats": _get_session_stats,
    "repositories": _get_repositories,
    "license": _get_license,
    "capacity_tier": _get_capacity_tier,
}

_ALL_DATASETS = list(_METHODS.keys())


async def collect_all(
    db: Session,
    provider: VeeamServerProvider,
    server_id: int,
) -> None:
    """Collect all datasets for a server and store as snapshots."""
    for dataset in _ALL_DATASETS:
        method = _METHODS[dataset]
        try:
            payload = await method(provider)
            _upsert_snapshot(db, server_id, dataset, payload)
        except Exception as exc:
            logger.warning("Failed to collect %s for server %s: %s", dataset, server_id, exc)
            _upsert_snapshot(db, server_id, dataset, {"success": False, "error": str(exc)})
