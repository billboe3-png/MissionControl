import urllib.request

url = "https://missioncontrol.optichosting.co.za/api/v1/debug/agent-plugin?name=veeam"
dest = r"C:\MissionControlAgent\agent\plugins\veeam_plugin.py"
with open(dest, "wb") as f:
    f.write(urllib.request.urlopen(url).read())
print("updated", dest)
