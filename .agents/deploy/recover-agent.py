import os
import subprocess
import urllib.request
import zipfile

BASE = r"C:\MissionControlAgent"
URL = "https://missioncontrol.optichosting.co.za/api/v1/agents/debug/bundle.zip?platform=windows"
PY = r"C:\Users\robert\AppData\Local\Programs\Python\Python312\python.exe"

os.makedirs(BASE, exist_ok=True)
zip_path = os.path.join(os.environ.get("TEMP", r"C:\Windows\Temp"), "mc-agent.zip")

print("[*] Downloading bundle ...")
with urllib.request.urlopen(URL, timeout=60) as r, open(zip_path, "wb") as f:
    f.write(r.read())
print("[+] Downloaded", os.path.getsize(zip_path), "bytes")

print("[*] Extracting ...")
with zipfile.ZipFile(zip_path) as z:
    for n in z.namelist():
        data = z.read(n)
        target = os.path.join(BASE, n.replace("/", os.sep))
        if n.endswith("/"):
            os.makedirs(target, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as f:
                f.write(data)
        print("   wrote", target)

print("[*] Installing Python deps ...")
subprocess.check_call([PY, "-m", "pip", "install", "--quiet", "httpx", "psutil", "pydantic", "pydantic-settings", "pyyaml", "packaging", "paramiko", "pywinrm"])

conf_dir = os.path.expanduser(r"~\.config\mission-control-agent")
os.makedirs(conf_dir, exist_ok=True)
with open(os.path.join(conf_dir, "config.yaml"), "w") as f:
    f.write("server_url: https://missioncontrol.optichosting.co.za\n")
    f.write("agent_name: CORHQROBERTB\n")
    f.write("heartbeat_interval: 30\n")
print("[+] Config written")

bat = os.path.join(BASE, "run-agent.bat")
with open(bat, "w") as f:
    f.write('"' + PY + '" -m agent.agent\n')

print("[*] Registering scheduled task ...")
subprocess.run(["schtasks.exe", "/Delete", "/TN", "MissionControlAgent", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.check_call(["schtasks.exe", "/Create", "/TN", "MissionControlAgent", "/TR", bat, "/SC", "ONLOGON", "/RL", "HIGHEST", "/F"])
print("[+] Scheduled task created")
