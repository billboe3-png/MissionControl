import platform

from app.platform.linux import LinuxPlatform
from app.platform.windows import WindowsPlatform

_provider = None


def get_platform():

    global _provider

    if _provider is not None:
        return _provider

    system = platform.system().lower()

    if system == "windows":
        _provider = WindowsPlatform()
    else:
        _provider = LinuxPlatform()

    return _provider
