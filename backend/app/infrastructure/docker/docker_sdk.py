import os

import docker
from docker.errors import DockerException


class DockerSdk:
    def __init__(self):
        self._client = None

    @property
    def client(self):

        if self._client is None:
            try:
                self._client = docker.DockerClient(
                    base_url=os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")
                )

            except DockerException:
                return None

            except Exception:
                return None

        return self._client

    @property
    def connected(self):

        return self.client is not None

    def ping(self):

        if self.client is None:
            return False

        try:
            return self.client.ping()

        except Exception:
            return False

    def version(self):

        if self.client is None:
            return {}

        try:
            return self.client.version()

        except Exception:
            return {}

    def info(self):

        if self.client is None:
            return {}

        try:
            return self.client.info()

        except Exception:
            return {}

    def containers(self):

        if self.client is None:
            return []

        try:
            return self.client.containers.list(all=True)

        except Exception:
            return []
