from .provider import DockerSdkProvider

_provider = None


def get_docker_provider():

    global _provider

    if _provider is None:
        _provider = DockerSdkProvider()

    return _provider
