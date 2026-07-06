from abc import ABC, abstractmethod


class DockerProvider(ABC):

    @abstractmethod
    async def info(self):
        ...

    @abstractmethod
    async def containers(self):
        ...

    @abstractmethod
    async def version(self):
        ...
