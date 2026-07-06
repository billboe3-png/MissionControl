from abc import ABC, abstractmethod


class PlatformBase(ABC):
    @abstractmethod
    async def status(self): ...

    @abstractmethod
    async def doctor(self): ...

    @abstractmethod
    async def docker_status(self): ...
