Write-Host ""
Write-Host "========================================="
Write-Host " Mission Control Sprint 4.6.1a"
Write-Host " Docker Scope Filtering"
Write-Host "========================================="
Write-Host ""

$root = Split-Path $PSScriptRoot -Parent

function Replace-OrAppend {
    param(
        [string]$File,
        [string]$Find,
        [string]$Replace
    )

    $text = Get-Content $File -Raw

    if ($text.Contains($Replace)) {
        return
    }

    if ($text.Contains($Find)) {
        $text = $text.Replace($Find, $Replace)
    }
    else {
        $text += "`r`n$Replace"
    }

    Set-Content $File $text -Encoding UTF8
}

###############################################################
# 1. CONFIG
###############################################################

$config = "$root\backend\app\core\config.py"

if (Test-Path $config) {

    $text = Get-Content $config -Raw

    if ($text -notmatch "compose_project_name") {

        $text = $text -replace "(environment:.*)", "`$1`r`n    compose_project_name: str = `"missioncontrol`""

        Set-Content $config $text -Encoding UTF8

        Write-Host "Updated config.py"
    }
}

###############################################################
# 2. ENV EXAMPLE
###############################################################

$envExample = "$root\.env.example"

if (Test-Path $envExample) {

    $text = Get-Content $envExample -Raw

    if ($text -notmatch "COMPOSE_PROJECT_NAME") {

        Add-Content $envExample ""
        Add-Content $envExample "# Docker"
        Add-Content $envExample "COMPOSE_PROJECT_NAME=missioncontrol"

        Write-Host "Updated .env.example"
    }
}

###############################################################
# 3. PROVIDER
###############################################################

$provider = "$root\backend\app\infrastructure\docker\provider.py"

if (Test-Path $provider) {

$text = @'
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
'@

    Set-Content $provider $text -Encoding UTF8

    Write-Host "Updated Docker provider"
}

###############################################################
# 4. VERIFY
###############################################################

Write-Host ""
Write-Host "========================================="
Write-Host " Sprint 4.6.1a Complete"
Write-Host "========================================="
Write-Host ""

Write-Host "Rebuild:"
Write-Host ""
Write-Host "docker compose up -d --build"
Write-Host ""
Write-Host "Verify:"
Write-Host ""
Write-Host "curl http://localhost/api/v1/docker"
Write-Host ""
Write-Host "Expected:"
Write-Host "  project = missioncontrol"
Write-Host "  Only Mission Control containers returned"
Write-Host "  No NetDisco containers"
Write-Host "  No UnitVote containers"
Write-Host ""