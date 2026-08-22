"""
Docker Plugin Cache

Provides convenient read access to cached Docker data.
All queries use synchronous SQLAlchemy sessions.
"""

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.plugins.installed.official_docker.models import (
    DockerComposeStack,
    DockerContainer,
    DockerHost,
    DockerImage,
    DockerNetwork,
    DockerVolume,
)

logger = logging.getLogger("plugin.docker.cache")


def _host_to_dict(h: DockerHost) -> dict[str, Any]:
    return {
        "id": h.id,
        "name": h.name,
        "hostname": h.hostname,
        "docker_version": h.docker_version,
        "api_version": h.api_version,
        "os": h.os,
        "kernel": h.kernel,
        "cpu_count": h.cpu_count,
        "memory_total": h.memory_total,
        "online": h.online,
        "last_error": h.last_error,
        "last_sync_at": h.last_sync_at.isoformat() if h.last_sync_at else None,
    }


def _container_to_dict(c: DockerContainer) -> dict[str, Any]:
    return {
        "id": c.id,
        "host_id": c.host_id,
        "container_id": c.container_id,
        "name": c.name,
        "image": c.image,
        "status": c.status,
        "state": c.state,
        "restart_count": c.restart_count,
        "cpu_pct": c.cpu_pct,
        "memory_pct": c.memory_pct,
        "memory_usage": c.memory_usage,
        "network_rx": c.network_rx,
        "network_tx": c.network_tx,
        "started_at": c.started_at.isoformat() if c.started_at else None,
        "health": c.health,
        "compose_project": c.compose_project,
    }


def _image_to_dict(img: DockerImage) -> dict[str, Any]:
    return {
        "id": img.id,
        "host_id": img.host_id,
        "image_id": img.image_id,
        "repository": img.repository,
        "tag": img.tag,
        "size": img.size,
        "created_at": img.created_at_ts.isoformat() if img.created_at_ts else None,
        "in_use": img.in_use,
    }


def _volume_to_dict(v: DockerVolume) -> dict[str, Any]:
    return {
        "id": v.id,
        "host_id": v.host_id,
        "name": v.name,
        "driver": v.driver,
        "mount_point": v.mount_point,
        "size": v.size,
        "usage": v.usage,
    }


def _network_to_dict(n: DockerNetwork) -> dict[str, Any]:
    return {
        "id": n.id,
        "host_id": n.host_id,
        "network_id": n.network_id,
        "name": n.name,
        "driver": n.driver,
        "scope": n.scope,
        "connected_containers": n.connected_containers,
    }


def _stack_to_dict(s: DockerComposeStack) -> dict[str, Any]:
    return {
        "id": s.id,
        "host_id": s.host_id,
        "project_name": s.project_name,
        "services": s.services,
        "running": s.running,
        "failed": s.failed,
        "status": s.status,
    }


class CacheManager:
    """Read-only access to cached Docker data."""

    def get_hosts(self, db: Session) -> list[dict[str, Any]]:
        rows = db.execute(
            select(DockerHost).order_by(DockerHost.name)
        ).scalars().all()
        return [_host_to_dict(r) for r in rows]

    def get_containers(
        self, db: Session, host_id: int | None = None,
        state: str | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(DockerContainer)
        if host_id:
            stmt = stmt.where(DockerContainer.host_id == host_id)
        if state:
            stmt = stmt.where(DockerContainer.state == state)
        rows = db.execute(stmt.order_by(DockerContainer.name)).scalars().all()
        return [_container_to_dict(r) for r in rows]

    def get_images(self, db: Session, host_id: int | None = None) -> list[dict[str, Any]]:
        stmt = select(DockerImage)
        if host_id:
            stmt = stmt.where(DockerImage.host_id == host_id)
        rows = db.execute(stmt.order_by(DockerImage.repository)).scalars().all()
        return [_image_to_dict(r) for r in rows]

    def get_volumes(self, db: Session, host_id: int | None = None) -> list[dict[str, Any]]:
        stmt = select(DockerVolume)
        if host_id:
            stmt = stmt.where(DockerVolume.host_id == host_id)
        rows = db.execute(stmt.order_by(DockerVolume.name)).scalars().all()
        return [_volume_to_dict(r) for r in rows]

    def get_networks(self, db: Session, host_id: int | None = None) -> list[dict[str, Any]]:
        stmt = select(DockerNetwork)
        if host_id:
            stmt = stmt.where(DockerNetwork.host_id == host_id)
        rows = db.execute(stmt.order_by(DockerNetwork.name)).scalars().all()
        return [_network_to_dict(r) for r in rows]

    def get_compose(self, db: Session, host_id: int | None = None) -> list[dict[str, Any]]:
        stmt = select(DockerComposeStack)
        if host_id:
            stmt = stmt.where(DockerComposeStack.host_id == host_id)
        rows = db.execute(
            stmt.order_by(DockerComposeStack.project_name)
        ).scalars().all()
        return [_stack_to_dict(r) for r in rows]

    def get_container_health(self, db: Session) -> dict[str, Any]:
        rows = db.execute(
            select(DockerContainer.state, func.count(DockerContainer.id))
            .group_by(DockerContainer.state)
        ).all()
        by_state = {row[0]: row[1] for row in rows}

        health_rows = db.execute(
            select(DockerContainer.health, func.count(DockerContainer.id))
            .where(DockerContainer.health.isnot(None))
            .group_by(DockerContainer.health)
        ).all()
        by_health = {row[0]: row[1] for row in health_rows}

        return {"by_state": by_state, "by_health": by_health}

    def get_resource_usage(self, db: Session, host_id: int | None = None) -> dict[str, Any]:
        stmt = select(DockerContainer).where(DockerContainer.state == "running")
        if host_id:
            stmt = stmt.where(DockerContainer.host_id == host_id)
        running = db.execute(stmt).scalars().all()

        total_cpu = sum(c.cpu_pct for c in running)
        total_memory = sum(c.memory_usage for c in running)
        total_net_rx = sum(c.network_rx for c in running)
        total_net_tx = sum(c.network_tx for c in running)

        host_rows = db.execute(select(DockerHost)).scalars().all()
        total_memory_capacity = sum(h.memory_total for h in host_rows if h.online)

        return {
            "running_count": len(running),
            "total_cpu_pct": round(total_cpu, 2),
            "total_memory_usage": total_memory,
            "total_memory_capacity": total_memory_capacity,
            "memory_pct": round(
                (total_memory / total_memory_capacity * 100) if total_memory_capacity else 0, 2
            ),
            "total_network_rx": total_net_rx,
            "total_network_tx": total_net_tx,
        }

    def get_summary(self, db: Session) -> dict[str, Any]:
        host_count = (db.execute(
            select(func.count(DockerHost.id))
        ).scalar()) or 0

        online_hosts = (db.execute(
            select(func.count(DockerHost.id)).where(DockerHost.online.is_(True))
        ).scalar()) or 0

        container_count = (db.execute(
            select(func.count(DockerContainer.id))
        ).scalar()) or 0

        running = (db.execute(
            select(func.count(DockerContainer.id)).where(DockerContainer.state == "running")
        ).scalar()) or 0

        stopped = (db.execute(
            select(func.count(DockerContainer.id)).where(DockerContainer.state == "exited")
        ).scalar()) or 0

        unhealthy = (db.execute(
            select(func.count(DockerContainer.id)).where(
                DockerContainer.health == "unhealthy"
            )
        ).scalar()) or 0

        restarting = (db.execute(
            select(func.count(DockerContainer.id)).where(
                DockerContainer.state == "restarting"
            )
        ).scalar()) or 0

        image_count = (db.execute(
            select(func.count(DockerImage.id))
        ).scalar()) or 0

        volume_count = (db.execute(
            select(func.count(DockerVolume.id))
        ).scalar()) or 0

        network_count = (db.execute(
            select(func.count(DockerNetwork.id))
        ).scalar()) or 0

        compose_count = (db.execute(
            select(func.count(DockerComposeStack.id))
        ).scalar()) or 0

        unhealthy_stacks = (db.execute(
            select(func.count(DockerComposeStack.id)).where(
                DockerComposeStack.status == "degraded"
            )
        ).scalar()) or 0

        resource = self.get_resource_usage(db)

        return {
            "available": online_hosts > 0 or host_count > 0,
            "host_count": host_count,
            "online_hosts": online_hosts,
            "container_count": container_count,
            "running": running,
            "stopped": stopped,
            "unhealthy": unhealthy,
            "restarting": restarting,
            "image_count": image_count,
            "volume_count": volume_count,
            "network_count": network_count,
            "compose_count": compose_count,
            "unhealthy_stacks": unhealthy_stacks,
            "total_cpu_pct": resource["total_cpu_pct"],
            "total_memory_usage": resource["total_memory_usage"],
            "total_memory_capacity": resource["total_memory_capacity"],
        }

    def get_last_sync(self, db: Session) -> str | None:
        latest = db.execute(
            select(func.max(DockerHost.last_sync_at))
        ).scalar()
        return latest.isoformat() if latest else None


cache_manager = CacheManager()
