import asyncio
import sys
sys.path.insert(0, "/app")

from app.providers.veeam.veeam_provider import VeeamRESTProvider
from app.core.config import get_settings
from app.core.security import CredentialCipher
from app.db import SessionLocal
from app.repositories.integration_profile_repository import IntegrationProfileRepository


async def test():
    settings = get_settings()
    cipher = CredentialCipher(settings.missioncontrol_secret_key)

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    db_url = f"postgresql://{os.environ.get('POSTGRES_USER','mission_control')}:{os.environ.get('POSTGRES_PASSWORD','mission_control')}@{os.environ.get('POSTGRES_HOST','postgres')}:{os.environ.get('POSTGRES_PORT','5432')}/{os.environ.get('POSTGRES_DB','mission_control')}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    profiles = IntegrationProfileRepository.get_all_enabled_by_type(db, "veeam")
    for profile in profiles:
        print(f"\n--- Profile: {profile.name} (data_source={profile.data_source}) ---")
        has_rest = bool(profile.base_url)
        has_ssh = bool(profile.ssh_host and profile.ssh_username)
        print(f"  has_rest={has_rest}, has_ssh={has_ssh}")

        if not has_rest and not has_ssh:
            print("  SKIP: no base_url or ssh")
            continue

        password = ""
        if profile.encrypted_secret:
            try:
                password = cipher.decrypt(profile.encrypted_secret)
            except Exception:
                pass

        ssh_password = ""
        if profile.ssh_password_encrypted:
            try:
                ssh_password = cipher.decrypt(profile.ssh_password_encrypted)
            except Exception:
                pass

        if has_rest:
            p = VeeamRESTProvider(
                base_url=profile.base_url or "",
                username=profile.username or "",
                password=password,
                timeout=profile.timeout or 30,
                verify_ssl=profile.verify_ssl if profile.verify_ssl is not None else True,
                ssh_host=profile.ssh_host or "",
                ssh_port=profile.ssh_port or 22,
                ssh_username=profile.ssh_username or "",
                ssh_password=ssh_password,
                data_source=profile.data_source or "both",
            )
        else:
            from app.providers.veeam.powershell_provider import VeeamPowerShellProvider
            p = VeeamPowerShellProvider(
                host=profile.ssh_host or "",
                port=5985,
                username=profile.ssh_username or "",
                password=ssh_password,
                timeout=profile.timeout or 60,
                transport="ssh",
                ssh_port=profile.ssh_port or 22,
            )

        result = await p.get_job_stats_daily(days=7)
        jobs = result.get("jobs", [])
        print(f"  success={result.get('success')}, jobs={len(jobs)}, error={result.get('error','none')}")
        for j in jobs[:3]:
            print(f"    {j.get('job_name')}: {j.get('dates', {})}")

    db.close()

asyncio.run(test())
