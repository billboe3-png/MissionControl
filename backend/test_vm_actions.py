import asyncio
import sys
sys.path.insert(0, "/app")

from app.db.database import get_db_session
from app.providers.hyperv.provider_factory import get_hyperv_provider


async def test():
    async for db in get_db_session():
        provider = await get_hyperv_provider(db, host_id=1)
        result = await provider.get_vms()
        if not result.get("items"):
            print("No VMs or error:", result)
            return
        for vm in result["items"][:3]:
            print("VM: {} ID={} State={}".format(vm["name"], vm["id"], vm["state"]))
        stopped = [vm for vm in result["items"] if vm["state"] != "running"]
        if stopped:
            vm = stopped[0]
            print("\nStarting {} (id={})...".format(vm["name"], vm["id"]))
            start_result = await provider.start_vm(vm["id"])
            print("Start result:", start_result)
        else:
            print("\nNo stopped VMs to start")
        break


asyncio.run(test())
