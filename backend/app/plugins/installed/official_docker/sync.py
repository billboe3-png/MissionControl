"""
Docker Plugin Sync

Background synchronization classes that pull data from Docker hosts
and write to local cache tables.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.plugins.installed.official_docker.models import (
    DockerComposeStack,
    DockerContainer,
    DockerHost,
    DockerImage,
    DockerNetwork,
    DockerVolume,
)

logger = logging.getLogger("plugin.docker.sync")


class HostSync:
    """Synchronize host info to local cache."""

    def sync(self, session: Session, client: Any, host_id: int) -> dict[str, int]:
        info = client.get_info_sync()
        version = client.get_version_sync()

        host = session.get(DockerHost, host_id)
        if host:
            host.docker_version = version.get("Version", "")
            host.api_version = version.get("ApiVersion", "")
            host.os = info.get("OperatingSystem", "")
            host.kernel = info.get("KernelVersion", "")
            host.cpu_count = int(info.get("NCPU", 0))
            host.memory_total = int(info.get("MemTotal", 0))
            host.online = True
            host.last_error = None
            host.last_sync_at = datetime.now(UTC)
        session.commit()
        return {"synced": 1}


class ContainerSync:
    """Synchronize containers from Docker API to local cache."""

    def sync(self, session: Session, client: Any, host_id: int) -> dict[str, int]:
        raw = client.get_containers_sync(all=True)
        synced = 0

        seen_ids: set[str] = set()
        for c in raw:
            cid = c.get("Id", "")
            if not cid:
                continue
            short_id = cid[:12]
            seen_ids.add(short_id)

            name = ""
            names = c.get("Names") or []
            if names:
                name = names[0].lstrip("/")

            image = c.get("Image", "")
            state = (c.get("State") or "").lower()
            status = c.get("Status", "")
            restart_count = c.get("RestartCount", 0) or 0

            labels = c.get("Labels") or {}
            compose_project = labels.get("com.docker.compose.project")

            health = None
            raw_health = c.get("Health")
            if isinstance(raw_health, dict):
                health = (raw_health.get("Status") or "").lower() or None

            started_str = c.get("StartedAt", "")
            started_at = None
            if started_str:
                try:
                    started_at = datetime.fromisoformat(
                        started_str.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            stmt = select(DockerContainer).where(
                DockerContainer.host_id == host_id,
                DockerContainer.container_id == short_id,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                existing.name = name
                existing.image = image
                existing.status = status
                existing.state = state
                existing.restart_count = restart_count
                existing.compose_project = compose_project
                existing.health = health
                existing.started_at = started_at
                existing.updated_at = datetime.now(UTC)
            else:
                session.add(DockerContainer(
                    host_id=host_id,
                    container_id=short_id,
                    name=name,
                    image=image,
                    status=status,
                    state=state,
                    restart_count=restart_count,
                    compose_project=compose_project,
                    health=health,
                    started_at=started_at,
                ))
            synced += 1

        active = session.execute(
            select(DockerContainer).where(DockerContainer.host_id == host_id)
        ).scalars().all()
        for row in active:
            if row.container_id not in seen_ids:
                session.delete(row)

        session.commit()
        logger.info("Container sync: %d containers synced", synced)
        return {"synced": synced}


class ImageSync:
    """Synchronize images from Docker API to local cache."""

    def sync(self, session: Session, client: Any, host_id: int) -> dict[str, int]:
        raw = client.get_images_sync()
        synced = 0

        seen_ids: set[str] = set()
        for img in raw:
            iid = img.get("Id", "")
            if not iid:
                continue
            short_id = iid.replace("sha256:", "")[:12]
            seen_ids.add(short_id)

            repo_tags = img.get("RepoTags") or []
            repository = "unknown"
            tag = "latest"
            if repo_tags:
                parts = repo_tags[0].rsplit(":", 1)
                repository = parts[0]
                if len(parts) > 1:
                    tag = parts[1]

            size = int(img.get("Size", 0))
            created_str = img.get("Created", "")
            created_at = None
            if created_str:
                try:
                    created_at = datetime.fromisoformat(
                        created_str.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            containers = client.get_containers_sync(all=True)
            in_use = any(
                short_id in (c.get("ImageID", "") or "")
                for c in containers
            )

            stmt = select(DockerImage).where(
                DockerImage.host_id == host_id,
                DockerImage.image_id == short_id,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                existing.repository = repository
                existing.tag = tag
                existing.size = size
                existing.created_at_ts = created_at
                existing.in_use = in_use
                existing.cached_at = datetime.now(UTC)
            else:
                session.add(DockerImage(
                    host_id=host_id,
                    image_id=short_id,
                    repository=repository,
                    tag=tag,
                    size=size,
                    created_at_ts=created_at,
                    in_use=in_use,
                ))
            synced += 1

        active = session.execute(
            select(DockerImage).where(DockerImage.host_id == host_id)
        ).scalars().all()
        for row in active:
            if row.image_id not in seen_ids:
                session.delete(row)

        session.commit()
        logger.info("Image sync: %d images synced", synced)
        return {"synced": synced}


class VolumeSync:
    """Synchronize volumes from Docker API to local cache."""

    def sync(self, session: Session, client: Any, host_id: int) -> dict[str, int]:
        raw = client.get_volumes_sync()
        synced = 0

        seen_names: set[str] = set()
        for v in raw:
            name = v.get("Name", "")
            if not name:
                continue
            seen_names.add(name)

            driver = v.get("Driver", "local")
            mountpoint = v.get("Mountpoint", "")

            stmt = select(DockerVolume).where(
                DockerVolume.host_id == host_id,
                DockerVolume.name == name,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                existing.driver = driver
                existing.mount_point = mountpoint
                existing.cached_at = datetime.now(UTC)
            else:
                session.add(DockerVolume(
                    host_id=host_id,
                    name=name,
                    driver=driver,
                    mount_point=mountpoint,
                ))
            synced += 1

        active = session.execute(
            select(DockerVolume).where(DockerVolume.host_id == host_id)
        ).scalars().all()
        for row in active:
            if row.name not in seen_names:
                session.delete(row)

        session.commit()
        logger.info("Volume sync: %d volumes synced", synced)
        return {"synced": synced}


class NetworkSync:
    """Synchronize networks from Docker API to local cache."""

    def sync(self, session: Session, client: Any, host_id: int) -> dict[str, int]:
        raw = client.get_networks_sync()
        synced = 0

        seen_ids: set[str] = set()
        for n in raw:
            nid = n.get("Id", "")
            if not nid:
                continue
            short_id = nid[:12]
            seen_ids.add(short_id)

            name = n.get("Name", "")
            driver = n.get("Driver", "bridge")
            scope = n.get("Scope", "local")
            containers = n.get("Containers") or {}
            connected = len(containers)

            stmt = select(DockerNetwork).where(
                DockerNetwork.host_id == host_id,
                DockerNetwork.network_id == short_id,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                existing.name = name
                existing.driver = driver
                existing.scope = scope
                existing.connected_containers = connected
                existing.cached_at = datetime.now(UTC)
            else:
                session.add(DockerNetwork(
                    host_id=host_id,
                    network_id=short_id,
                    name=name,
                    driver=driver,
                    scope=scope,
                    connected_containers=connected,
                ))
            synced += 1

        active = session.execute(
            select(DockerNetwork).where(DockerNetwork.host_id == host_id)
        ).scalars().all()
        for row in active:
            if row.network_id not in seen_ids:
                session.delete(row)

        session.commit()
        logger.info("Network sync: %d networks synced", synced)
        return {"synced": synced}


class ComposeSync:
    """Synchronize Compose projects from Docker container labels."""

    def sync(self, session: Session, client: Any, host_id: int) -> dict[str, int]:
        projects = client.get_compose_projects_sync()
        synced = 0

        seen_names: set[str] = set()
        for p in projects:
            name = p.get("name", "")
            if not name:
                continue
            seen_names.add(name)

            services = int(p.get("services", 0))
            running = int(p.get("running", 0))
            failed = int(p.get("failed", 0))
            status = p.get("status", "unknown")

            stmt = select(DockerComposeStack).where(
                DockerComposeStack.host_id == host_id,
                DockerComposeStack.project_name == name,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                existing.services = services
                existing.running = running
                existing.failed = failed
                existing.status = status
                existing.cached_at = datetime.now(UTC)
            else:
                session.add(DockerComposeStack(
                    host_id=host_id,
                    project_name=name,
                    services=services,
                    running=running,
                    failed=failed,
                    status=status,
                ))
            synced += 1

        active = session.execute(
            select(DockerComposeStack).where(DockerComposeStack.host_id == host_id)
        ).scalars().all()
        for row in active:
            if row.project_name not in seen_names:
                session.delete(row)

        session.commit()
        logger.info("Compose sync: %d projects synced", synced)
        return {"synced": synced}
