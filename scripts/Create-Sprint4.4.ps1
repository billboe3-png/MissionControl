$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================="
Write-Host " Mission Control Sprint 4.4"
Write-Host " Docker Service API"
Write-Host "========================================="
Write-Host ""

#------------------------------------------------------------
# backend/app/services/docker_service.py
#------------------------------------------------------------

$dockerService = @'
import subprocess


def run_command(command: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return False, result.stderr.strip()

        return True, result.stdout.strip()

    except Exception:
        return False, ""


async def get_docker_status():

    engine_ok, _ = run_command(["docker", "info"])

    compose_ok, _ = run_command(["docker", "compose", "version"])

    containers = []

    ok, output = run_command(
        [
            "docker",
            "ps",
            "--format",
            "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"
        ]
    )

    if ok and output:

        for line in output.splitlines():

            name, image, status, ports = line.split("|")

            containers.append(
                {
                    "name": name,
                    "image": image,
                    "status": status,
                    "ports": ports
                }
            )

    return {
        "engine": "running" if engine_ok else "offline",
        "compose": "available" if compose_ok else "missing",
        "container_count": len(containers),
        "containers": containers
    }
'@

Set-Content backend/app/services/docker_service.py $dockerService

Write-Host "Created docker_service.py"

#------------------------------------------------------------
# backend/app/services/__init__.py
#------------------------------------------------------------

$init = Get-Content backend/app/services/__init__.py -Raw

if ($init -notmatch "get_docker_status") {

    $init += @"

from .docker_service import get_docker_status
"@
}

Set-Content backend/app/services/__init__.py $init

Write-Host "Updated services/__init__.py"

#------------------------------------------------------------
# backend/app/routers/docker.py
#------------------------------------------------------------

$router = @'
from fastapi import APIRouter

from app.services import get_docker_status

router = APIRouter(tags=["docker"])


@router.get("/docker")
async def docker():

    return await get_docker_status()
'@

Set-Content backend/app/routers/docker.py $router

Write-Host "Updated routers/docker.py"

#------------------------------------------------------------
# backend/app/main.py
#------------------------------------------------------------

$main = "backend/app/main.py"

$content = Get-Content $main -Raw

if ($content -notmatch "from app\.routers import docker") {

$content = $content.Replace(

"from app.routers import doctor",

@"
from app.routers import doctor
from app.routers import docker
"@
)

}

if ($content -notmatch "include_router\(docker\.router") {

$content = $content.Replace(

'app.include_router(doctor.router, prefix="/api/v1")',

@'
app.include_router(doctor.router, prefix="/api/v1")
app.include_router(docker.router, prefix="/api/v1")
'@
)

}

Set-Content $main $content

Write-Host "Updated main.py"

Write-Host ""
Write-Host "========================================="
Write-Host "Sprint 4.4 files generated"
Write-Host "========================================="
Write-Host ""
Write-Host "Next:"
Write-Host ""
Write-Host "docker compose up -d --build"
Write-Host ""
Write-Host "Verify:"
Write-Host ""
Write-Host "curl http://localhost/api/v1/docker"