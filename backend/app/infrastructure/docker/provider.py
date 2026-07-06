from app.core.config import get_settings

from .base import DockerProvider
from .docker_sdk import DockerSdk


class DockerSdkProvider(DockerProvider):

    def __init__(self):

        self.sdk = DockerSdk()
        self.settings = get_settings()


    async def info(self):

        return self.sdk.info()


    async def version(self):

        return self.sdk.version()


    async def containers(self):

        results = []

        project = self.settings.compose_project_name

        containers = self.sdk.client.containers.list(
            all=True,
            filters={
                "label": f"com.docker.compose.project={project}"
            }
        )

        for container in containers:

            try:

                results.append(
                    {
                        "id": container.short_id,
                        "name": container.name,
                        "image": container.image.tags[0] if container.image.tags else "<none>",
                        "status": container.status,
                    }
                )

            except Exception:
                pass

        return results
