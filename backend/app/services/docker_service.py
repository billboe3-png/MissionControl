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
