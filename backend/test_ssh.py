import paramiko
import sys

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    c.connect('192.168.10.49', 22, 'kg\\administrator', timeout=10)
except TypeError:
    # password needed
    print("Need password")
    sys.exit(1)

cmd = 'pwsh.exe -NoProfile -Command "Get-ChildItem \'C:\\Program Files\\PostgreSQL\\\' | Select-Object Name"'
_, out, err = c.exec_command(cmd, timeout=15)
print("OUT:", out.read().decode())
print("ERR:", err.read().decode())
c.close()
