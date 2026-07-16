"""Seed built-in automation playbooks."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.playbook import Playbook
from app.models.db.playbook_step import PlaybookStep
from app.models.db.playbook_variable import PlaybookVariable

PLAYBOOKS = [
    # ------------------------------------------------------------------ #
    # Windows (8)                                                         #
    # ------------------------------------------------------------------ #
    {
        "name": "Windows: Restart Service",
        "description": "Restart a Windows service on a remote host",
        "category": "Windows",
        "steps": [
            {"name": "Stop Service", "step_type": "powershell", "provider": "ssh",
             "command": "Stop-Service -Name '{{service_name}}' -Force", "step_order": 1},
            {"name": "Wait", "step_type": "powershell", "provider": "ssh",
             "command": "Start-Sleep -Seconds 5", "step_order": 2},
            {"name": "Start Service", "step_type": "powershell", "provider": "ssh",
             "command": "Start-Service -Name '{{service_name}}'", "step_order": 3},
            {"name": "Verify Running", "step_type": "powershell", "provider": "ssh",
             "command": "Get-Service -Name '{{service_name}}' | Select-Object -ExpandProperty Status",
             "step_order": 4},
        ],
        "variables": [{"name": "service_name", "required": True, "sensitive": False}],
    },
    {
        "name": "Windows: Disk Cleanup",
        "description": "Clean temp files and Windows Update cache",
        "category": "Windows",
        "steps": [
            {"name": "Clear Temp", "step_type": "powershell", "provider": "ssh",
             "command": "Remove-Item -Path '$env:TEMP\\*' -Recurse -Force -ErrorAction SilentlyContinue",
             "step_order": 1},
            {"name": "Clear Windows Update Cache", "step_type": "powershell", "provider": "ssh",
             "command": "Stop-Service wuauserv; Remove-Item -Path 'C:\\Windows\\SoftwareDistribution\\Download\\*' -Recurse -Force; Start-Service wuauserv",
             "step_order": 2},
            {"name": "Report Disk Space", "step_type": "powershell", "provider": "ssh",
             "command": "Get-PSDrive C | Select-Object Used, Free",
             "step_order": 3},
        ],
    },
    {
        "name": "Windows: Check Event Logs",
        "description": "Query recent error events from Windows Event Log",
        "category": "Windows",
        "steps": [
            {"name": "Query Errors", "step_type": "powershell", "provider": "ssh",
             "command": "Get-EventLog -LogName System -EntryType Error -Newest 20 | Select-Object TimeGenerated, Source, Message | Format-Table -AutoSize",
             "step_order": 1},
        ],
    },
    {
        "name": "Windows: IIS App Pool Restart",
        "description": "Recycle an IIS Application Pool",
        "category": "Windows",
        "steps": [
            {"name": "Recycle App Pool", "step_type": "powershell", "provider": "ssh",
             "command": "Import-Module WebAdministration; Restart-WebAppPool -Name '{{pool_name}}'",
             "step_order": 1},
            {"name": "Verify State", "step_type": "powershell", "provider": "ssh",
             "command": "Import-Module WebAdministration; Get-WebAppPoolState -Name '{{pool_name}}' | Select-Object -ExpandProperty Value",
             "step_order": 2},
        ],
        "variables": [{"name": "pool_name", "required": True}],
    },
    {
        "name": "Windows: Windows Update Check",
        "description": "Check for pending Windows Updates",
        "category": "Windows",
        "steps": [
            {"name": "Check Updates", "step_type": "powershell", "provider": "ssh",
             "command": "(New-Object -ComObject Microsoft.Update.Session).CreateUpdateSearcher().Search('IsInstalled=0').Updates | Select-Object Title, Severity | Format-Table -AutoSize",
             "step_order": 1},
        ],
    },
    {
        "name": "Windows: User Account Audit",
        "description": "List local user accounts and their status",
        "category": "Windows",
        "steps": [
            {"name": "List Users", "step_type": "powershell", "provider": "ssh",
             "command": "Get-LocalUser | Select-Object Name, Enabled, LastLogon | Format-Table -AutoSize",
             "step_order": 1},
            {"name": "List Admins", "step_type": "powershell", "provider": "ssh",
             "command": "Get-LocalGroupMember -Group 'Administrators' | Select-Object Name, PrincipalSource | Format-Table -AutoSize",
             "step_order": 2},
        ],
    },
    {
        "name": "Windows: SSL Certificate Check",
        "description": "Check SSL certificate expiry for a hostname",
        "category": "Windows",
        "steps": [
            {"name": "Check Cert", "step_type": "powershell", "provider": "ssh",
             "command": "$cert = [System.Net.Dns]::GetHostAddresses('{{hostname}}') | ForEach-Object { try { $tcp = New-Object System.Net.Sockets.TcpClient($_.IPAddressToString, {{port}}); $ssl = New-Object System.Net.Security.SslStream($tcp.GetStream(), $false, {$true}); $ssl.AuthenticateAsClient('{{hostname}}'); $ssl.RemoteCertificate } catch {} } | Select-Object -First 1; Write-Output \"Expires: $($cert.GetExpirationDateFormatted())\"",
             "step_order": 1},
        ],
        "variables": [{"name": "hostname", "required": True}, {"name": "port", "default_value": "443"}],
    },
    {
        "name": "Windows: Backup IIS Config",
        "description": "Backup IIS configuration to a timestamped file",
        "category": "Windows",
        "steps": [
            {"name": "Backup Config", "step_type": "powershell", "provider": "ssh",
             "command": "Copy-Item 'C:\\Windows\\System32\\inetsrv\\config\\applicationHost.config' -Destination 'C:\\Backups\\IIS\\applicationHost_$(Get-Date -Format yyyyMMdd_HHmmss).config'",
             "step_order": 1},
        ],
    },
    # ------------------------------------------------------------------ #
    # Linux (8)                                                           #
    # ------------------------------------------------------------------ #
    {
        "name": "Linux: System Health Check",
        "description": "Comprehensive system health check (CPU, memory, disk, services)",
        "category": "Linux",
        "steps": [
            {"name": "CPU Load", "step_type": "bash", "provider": "ssh",
             "command": "uptime", "step_order": 1},
            {"name": "Memory", "step_type": "bash", "provider": "ssh",
             "command": "free -h", "step_order": 2},
            {"name": "Disk", "step_type": "bash", "provider": "ssh",
             "command": "df -h /", "step_order": 3},
            {"name": "Failed Services", "step_type": "bash", "provider": "ssh",
             "command": "systemctl list-units --state=failed --no-pager || true", "step_order": 4},
        ],
    },
    {
        "name": "Linux: Log Rotation",
        "description": "Force log rotation and clean old logs",
        "category": "Linux",
        "steps": [
            {"name": "Force Logrotate", "step_type": "bash", "provider": "ssh",
             "command": "logrotate -f /etc/logrotate.conf", "step_order": 1},
            {"name": "Clean Old Logs", "step_type": "bash", "provider": "ssh",
             "command": "find /var/log -name '*.gz' -mtime +30 -delete", "step_order": 2},
        ],
    },
    {
        "name": "Linux: Security Audit",
        "description": "Basic security audit (SSH config, open ports, failed logins)",
        "category": "Linux",
        "steps": [
            {"name": "SSH Config Check", "step_type": "bash", "provider": "ssh",
             "command": "grep -E 'PermitRootLogin|PasswordAuthentication|PubkeyAuthentication' /etc/ssh/sshd_config", "step_order": 1},
            {"name": "Open Ports", "step_type": "bash", "provider": "ssh",
             "command": "ss -tlnp", "step_order": 2},
            {"name": "Failed Logins", "step_type": "bash", "provider": "ssh",
             "command": "journalctl _SYSTEMD_UNIT=sshd.service --no-pager -n 20 2>/dev/null || tail -20 /var/log/auth.log 2>/dev/null || echo 'No auth logs available'",
             "step_order": 3},
        ],
    },
    {
        "name": "Linux: Certificate Renewal",
        "description": "Renew Let's Encrypt certificates",
        "category": "Linux",
        "steps": [
            {"name": "Renew Certs", "step_type": "bash", "provider": "ssh",
             "command": "certbot renew --quiet", "step_order": 1},
            {"name": "Reload Nginx", "step_type": "bash", "provider": "ssh",
             "command": "systemctl reload nginx", "step_order": 2},
        ],
    },
    {
        "name": "Linux: Package Updates",
        "description": "Update system packages and show changelog",
        "category": "Linux",
        "steps": [
            {"name": "Update Cache", "step_type": "bash", "provider": "ssh",
             "command": "apt-get update -qq", "step_order": 1},
            {"name": "Upgrade", "step_type": "bash", "provider": "ssh",
             "command": "DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq", "step_order": 2},
            {"name": "Autoremove", "step_type": "bash", "provider": "ssh",
             "command": "apt-get autoremove -y -qq", "step_order": 3},
        ],
    },
    {
        "name": "Linux: Docker Cleanup",
        "description": "Clean up Docker images, containers, and volumes",
        "category": "Linux",
        "steps": [
            {"name": "Remove Stopped", "step_type": "bash", "provider": "ssh",
             "command": "docker container prune -f", "step_order": 1},
            {"name": "Remove Dangling", "step_type": "bash", "provider": "ssh",
             "command": "docker image prune -f", "step_order": 2},
            {"name": "Remove Unused Volumes", "step_type": "bash", "provider": "ssh",
             "command": "docker volume prune -f", "step_order": 3},
            {"name": "Disk Usage", "step_type": "bash", "provider": "ssh",
             "command": "docker system df", "step_order": 4},
        ],
    },
    {
        "name": "Linux: Nginx Config Test",
        "description": "Test and reload Nginx configuration",
        "category": "Linux",
        "steps": [
            {"name": "Test Config", "step_type": "bash", "provider": "ssh",
             "command": "nginx -t", "step_order": 1},
            {"name": "Reload", "step_type": "bash", "provider": "ssh",
             "command": "systemctl reload nginx", "step_order": 2},
        ],
    },
    {
        "name": "Linux: Database Backup",
        "description": "Backup PostgreSQL database with timestamp",
        "category": "Linux",
        "steps": [
            {"name": "pg_dump", "step_type": "bash", "provider": "ssh",
             "command": "pg_dump -U {{db_user}} {{db_name}} | gzip > /backups/postgres/{{db_name}}_$(date +%Y%m%d_%H%M%S).sql.gz",
             "step_order": 1},
            {"name": "Clean Old Backups", "step_type": "bash", "provider": "ssh",
             "command": "find /backups/postgres -name '*.sql.gz' -mtime +{{retention_days}} -delete",
             "step_order": 2},
        ],
        "variables": [
            {"name": "db_user", "required": True},
            {"name": "db_name", "required": True},
            {"name": "retention_days", "default_value": "30"},
        ],
    },
    # ------------------------------------------------------------------ #
    # Docker (8)                                                          #
    # ------------------------------------------------------------------ #
    {
        "name": "Docker: Container Status",
        "description": "Show status of all Docker containers",
        "category": "Docker",
        "steps": [
            {"name": "List Containers", "step_type": "bash", "provider": "ssh",
             "command": "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}'",
             "step_order": 1},
            {"name": "Disk Usage", "step_type": "bash", "provider": "ssh",
             "command": "docker system df", "step_order": 2},
        ],
    },
    {
        "name": "Docker: Restart Container",
        "description": "Restart a specific Docker container",
        "category": "Docker",
        "steps": [
            {"name": "Restart", "step_type": "bash", "provider": "ssh",
             "command": "docker restart {{container_name}}", "step_order": 1},
            {"name": "Verify", "step_type": "bash", "provider": "ssh",
             "command": "docker inspect --format '{{.State.Status}}' {{container_name}}",
             "step_order": 2},
        ],
        "variables": [{"name": "container_name", "required": True}],
    },
    {
        "name": "Docker: Full Cleanup",
        "description": "Remove all stopped containers, unused networks, dangling images",
        "category": "Docker",
        "steps": [
            {"name": "Prune All", "step_type": "bash", "provider": "ssh",
             "command": "docker system prune -af --volumes", "step_order": 1},
            {"name": "Disk Usage", "step_type": "bash", "provider": "ssh",
             "command": "docker system df", "step_order": 2},
        ],
    },
    {
        "name": "Docker: Pull and Restart",
        "description": "Pull latest image and restart a container",
        "category": "Docker",
        "steps": [
            {"name": "Pull Image", "step_type": "bash", "provider": "ssh",
             "command": "docker pull {{image}}", "step_order": 1},
            {"name": "Stop Container", "step_type": "bash", "provider": "ssh",
             "command": "docker stop {{container_name}}", "step_order": 2},
            {"name": "Remove Container", "step_type": "bash", "provider": "ssh",
             "command": "docker rm {{container_name}}", "step_order": 3},
            {"name": "Run New", "step_type": "bash", "provider": "ssh",
             "command": "docker run -d --name {{container_name}} {{run_args}} {{image}}",
             "step_order": 4, "continue_on_failure": True},
        ],
        "variables": [
            {"name": "image", "required": True},
            {"name": "container_name", "required": True},
            {"name": "run_args", "default_value": ""},
        ],
    },
    {
        "name": "Docker: Compose Up",
        "description": "Run docker-compose up in a specified directory",
        "category": "Docker",
        "steps": [
            {"name": "Compose Up", "step_type": "bash", "provider": "ssh",
             "command": "cd {{compose_dir}} && docker compose up -d --build",
             "step_order": 1},
            {"name": "Verify", "step_type": "bash", "provider": "ssh",
             "command": "cd {{compose_dir}} && docker compose ps",
             "step_order": 2},
        ],
        "variables": [{"name": "compose_dir", "required": True}],
    },
    {
        "name": "Docker: Container Logs",
        "description": "Fetch recent logs from a container",
        "category": "Docker",
        "steps": [
            {"name": "Logs", "step_type": "bash", "provider": "ssh",
             "command": "docker logs --tail {{lines}} {{container_name}}",
             "step_order": 1},
        ],
        "variables": [
            {"name": "container_name", "required": True},
            {"name": "lines", "default_value": "100"},
        ],
    },
    {
        "name": "Docker: Health Check All",
        "description": "Check health status of all containers",
        "category": "Docker",
        "steps": [
            {"name": "Health Check", "step_type": "bash", "provider": "ssh",
             "command": "docker ps --format '{{.Names}}: {{.Status}}' | grep -v 'Up'",
             "step_order": 1, "continue_on_failure": True},
        ],
    },
    {
        "name": "Docker: Export Container",
        "description": "Export a container filesystem as a tarball",
        "category": "Docker",
        "steps": [
            {"name": "Export", "step_type": "bash", "provider": "ssh",
             "command": "docker export {{container_name}} | gzip > /backups/docker/{{container_name}}_$(date +%Y%m%d_%H%M%S).tar.gz",
             "step_order": 1},
        ],
        "variables": [{"name": "container_name", "required": True}],
    },
    # ------------------------------------------------------------------ #
    # Zabbix (5)                                                          #
    # ------------------------------------------------------------------ #
    {
        "name": "Zabbix: Check Host Availability",
        "description": "Check if monitored hosts are available",
        "category": "Zabbix",
        "steps": [
            {"name": "API Login", "step_type": "http", "provider": "http",
             "command": '{"method": "POST", "url": "{{zabbix_url}}/api_jsonrpc.php", "headers": {"Content-Type": "application/json-rpc"}, "body": {"jsonrpc": "2.0", "method": "user.login", "params": {"user": "{{zabbix_user}}", "password": "{{zabbix_pass}}"}, "id": 1}}',
             "step_order": 1},
        ],
        "variables": [
            {"name": "zabbix_url", "required": True},
            {"name": "zabbix_user", "required": True},
            {"name": "zabbix_pass", "required": True, "sensitive": True},
        ],
    },
    {
        "name": "Zabbix: Acknowledge Problems",
        "description": "Acknowledge all recent problems",
        "category": "Zabbix",
        "steps": [
            {"name": "List Problems", "step_type": "bash", "provider": "ssh",
             "command": "echo 'Use Zabbix API to acknowledge problems'", "step_order": 1},
        ],
    },
    {
        "name": "Zabbix: Export Hosts",
        "description": "Export host configuration from Zabbix",
        "category": "Zabbix",
        "steps": [
            {"name": "Export", "step_type": "bash", "provider": "ssh",
             "command": "echo 'Export Zabbix hosts via API'", "step_order": 1},
        ],
    },
    {
        "name": "Zabbix: Clear Maintenance",
        "description": "Clear all maintenance windows",
        "category": "Zabbix",
        "steps": [
            {"name": "Clear", "step_type": "bash", "provider": "ssh",
             "command": "echo 'Clear Zabbix maintenance via API'", "step_order": 1},
        ],
    },
    {
        "name": "Zabbix: Agent Restart",
        "description": "Restart Zabbix agent on target hosts",
        "category": "Zabbix",
        "steps": [
            {"name": "Restart Agent", "step_type": "bash", "provider": "ssh",
             "command": "systemctl restart zabbix-agent", "step_order": 1},
        ],
    },
    # ------------------------------------------------------------------ #
    # Remote Operations (6)                                               #
    # ------------------------------------------------------------------ #
    {
        "name": "Remote: Execute Command",
        "description": "Execute an arbitrary command on a remote host",
        "category": "Remote",
        "steps": [
            {"name": "Execute", "step_type": "bash", "provider": "ssh",
             "command": "{{command}}", "step_order": 1},
        ],
        "variables": [{"name": "command", "required": True}],
    },
    {
        "name": "Remote: File Transfer",
        "description": "Transfer a file to a remote host",
        "category": "Remote",
        "steps": [
            {"name": "Transfer", "step_type": "bash", "provider": "ssh",
             "command": "scp -o StrictHostKeyChecking=no {{source_file}} {{dest_user}}@{{dest_host}}:{{dest_path}}",
             "step_order": 1},
        ],
        "variables": [
            {"name": "source_file", "required": True},
            {"name": "dest_user", "required": True},
            {"name": "dest_host", "required": True},
            {"name": "dest_path", "required": True},
        ],
    },
    {
        "name": "Remote: Disk Space Report",
        "description": "Check disk space on multiple remote hosts",
        "category": "Remote",
        "steps": [
            {"name": "Disk Report", "step_type": "bash", "provider": "ssh",
             "command": "df -h | awk '$5 > 80 {print \"WARNING: \" $0}'", "step_order": 1,
             "continue_on_failure": True},
        ],
    },
    {
        "name": "Remote: Process Monitor",
        "description": "Check top processes by CPU and memory",
        "category": "Remote",
        "steps": [
            {"name": "Top CPU", "step_type": "bash", "provider": "ssh",
             "command": "ps aux --sort=-%cpu | head -10", "step_order": 1},
            {"name": "Top Memory", "step_type": "bash", "provider": "ssh",
             "command": "ps aux --sort=-%mem | head -10", "step_order": 2},
        ],
    },
    {
        "name": "Remote: Network Connectivity",
        "description": "Test network connectivity to target hosts",
        "category": "Remote",
        "steps": [
            {"name": "Ping Test", "step_type": "bash", "provider": "ssh",
             "command": "ping -c 3 {{target_host}}", "step_order": 1},
            {"name": "Port Check", "step_type": "bash", "provider": "ssh",
             "command": "nc -zv {{target_host}} {{target_port}} -w 5",
             "step_order": 2, "continue_on_failure": True},
        ],
        "variables": [
            {"name": "target_host", "required": True},
            {"name": "target_port", "default_value": "22"},
        ],
    },
    {
        "name": "Remote: Batch SSH Setup",
        "description": "Set up SSH key-based auth on multiple hosts",
        "category": "Remote",
        "steps": [
            {"name": "Copy Key", "step_type": "bash", "provider": "ssh",
             "command": "ssh-copy-id -o StrictHostKeyChecking=no {{user}}@{{host}}",
             "step_order": 1},
        ],
        "variables": [
            {"name": "user", "required": True},
            {"name": "host", "required": True},
        ],
    },
    # ------------------------------------------------------------------ #
    # Hyper-V (6)                                                         #
    # ------------------------------------------------------------------ #
    {
        "name": "Hyper-V: VM Status",
        "description": "Check status of all Hyper-V virtual machines",
        "category": "Hyper-V",
        "steps": [
            {"name": "List VMs", "step_type": "powershell", "provider": "ssh",
             "command": "Get-VM | Select-Object Name, State, CPUUsage, MemoryAssigned, Uptime | Format-Table -AutoSize",
             "step_order": 1},
        ],
    },
    {
        "name": "Hyper-V: Restart VM",
        "description": "Restart a Hyper-V virtual machine",
        "category": "Hyper-V",
        "steps": [
            {"name": "Stop VM", "step_type": "powershell", "provider": "ssh",
             "command": "Stop-VM -Name '{{vm_name}}' -Force", "step_order": 1},
            {"name": "Start VM", "step_type": "powershell", "provider": "ssh",
             "command": "Start-VM -Name '{{vm_name}}'", "step_order": 2},
        ],
        "variables": [{"name": "vm_name", "required": True}],
    },
    {
        "name": "Hyper-V: Checkpoint VM",
        "description": "Create a checkpoint (snapshot) of a VM",
        "category": "Hyper-V",
        "steps": [
            {"name": "Create Checkpoint", "step_type": "powershell", "provider": "ssh",
             "command": "Checkpoint-VM -Name '{{vm_name}}' -SnapshotName 'Auto-$(Get-Date -Format yyyyMMdd_HHmmss)'",
             "step_order": 1},
        ],
        "variables": [{"name": "vm_name", "required": True}],
    },
    {
        "name": "Hyper-V: Export VM",
        "description": "Export a Hyper-V virtual machine",
        "category": "Hyper-V",
        "steps": [
            {"name": "Export", "step_type": "powershell", "provider": "ssh",
             "command": "Export-VM -Name '{{vm_name}}' -Path '{{export_path}}'",
             "step_order": 1},
        ],
        "variables": [
            {"name": "vm_name", "required": True},
            {"name": "export_path", "required": True},
        ],
    },
    {
        "name": "Hyper-V: Add Disk",
        "description": "Add a new virtual disk to a VM",
        "category": "Hyper-V",
        "steps": [
            {"name": "Add Disk", "step_type": "powershell", "provider": "ssh",
             "command": "New-VHD -Path '{{vhd_path}}' -SizeBytes {{size_gb}}GB -Dynamic; Add-VMHardDiskDrive -VMName '{{vm_name}}' -Path '{{vhd_path}}'",
             "step_order": 1},
        ],
        "variables": [
            {"name": "vm_name", "required": True},
            {"name": "vhd_path", "required": True},
            {"name": "size_gb", "default_value": "50"},
        ],
    },
    {
        "name": "Hyper-V: Network Config",
        "description": "List and configure VM network adapters",
        "category": "Hyper-V",
        "steps": [
            {"name": "List Adapters", "step_type": "powershell", "provider": "ssh",
             "command": "Get-VMNetworkAdapter -VMName '{{vm_name}}' | Select-Object Name, SwitchName, MacAddress | Format-Table -AutoSize",
             "step_order": 1},
        ],
        "variables": [{"name": "vm_name", "required": True}],
    },
    # ------------------------------------------------------------------ #
    # Microsoft 365 (5)                                                   #
    # ------------------------------------------------------------------ #
    {
        "name": "M365: Mailbox Size Report",
        "description": "Report mailbox sizes for all users",
        "category": "M365",
        "steps": [
            {"name": "Connect", "step_type": "powershell", "provider": "ssh",
             "command": "Connect-ExchangeOnline -UserPrincipalName '{{admin_user}}'", "step_order": 1},
            {"name": "Report", "step_type": "powershell", "provider": "ssh",
             "command": "Get-Mailbox -ResultSize Unlimited | Get-MailboxStatistics | Select-Object DisplayName, TotalItemSize, ItemCount | Sort-Object TotalItemSize -Descending | Format-Table -AutoSize",
             "step_order": 2},
        ],
        "variables": [{"name": "admin_user", "required": True}],
    },
    {
        "name": "M365: License Report",
        "description": "Report Microsoft 365 license usage",
        "category": "M365",
        "steps": [
            {"name": "Report", "step_type": "powershell", "provider": "ssh",
             "command": "Get-MsolAccountSku | Select-Object AccountSkuId, ActiveUnits, ConsumedUnits | Format-Table -AutoSize",
             "step_order": 1},
        ],
    },
    {
        "name": "M365: User Provisioning",
        "description": "Create a new M365 user with license assignment",
        "category": "M365",
        "steps": [
            {"name": "Create User", "step_type": "powershell", "provider": "ssh",
             "command": "New-MsolUser -UserPrincipalName '{{upn}}' -DisplayName '{{display_name}}' -FirstName '{{first_name}}' -LastName '{{last_name}}' -UsageLocation '{{location}}'",
             "step_order": 1},
            {"name": "Assign License", "step_type": "powershell", "provider": "ssh",
             "command": "Set-MsolUserLicense -UserPrincipalName '{{upn}}' -AddLicenses '{{sku_id}}'",
             "step_order": 2},
        ],
        "variables": [
            {"name": "upn", "required": True},
            {"name": "display_name", "required": True},
            {"name": "first_name", "required": True},
            {"name": "last_name", "required": True},
            {"name": "location", "default_value": "ZA"},
            {"name": "sku_id", "required": True},
        ],
    },
    {
        "name": "M365: Distribution List Members",
        "description": "List members of a distribution group",
        "category": "M365",
        "steps": [
            {"name": "List Members", "step_type": "powershell", "provider": "ssh",
             "command": "Get-DistributionGroupMember -Identity '{{group_name}}' | Select-Object Name, PrimarySmtpAddress | Format-Table -AutoSize",
             "step_order": 1},
        ],
        "variables": [{"name": "group_name", "required": True}],
    },
    {
        "name": "M365: Conditional Access Audit",
        "description": "List conditional access policies",
        "category": "M365",
        "steps": [
            {"name": "List Policies", "step_type": "powershell", "provider": "ssh",
             "command": "Get-MgIdentityConditionalAccessPolicy | Select-Object DisplayName, State | Format-Table -AutoSize",
             "step_order": 1},
        ],
    },
    # ------------------------------------------------------------------ #
    # Active Directory (6)                                                #
    # ------------------------------------------------------------------ #
    {
        "name": "AD: User Audit",
        "description": "Audit Active Directory user accounts",
        "category": "AD",
        "steps": [
            {"name": "Disabled Accounts", "step_type": "powershell", "provider": "ssh",
             "command": "Get-ADUser -Filter {Enabled -eq $false} -Properties LastLogonDate | Select-Object Name, SamAccountName, LastLogonDate | Format-Table -AutoSize",
             "step_order": 1},
            {"name": "Password Age", "step_type": "powershell", "provider": "ssh",
             "command": "Get-ADUser -Filter * -Properties PasswordLastSet | Where-Object { $_.PasswordLastSet -lt (Get-Date).AddDays(-90) } | Select-Object Name, SamAccountName, PasswordLastSet | Format-Table -AutoSize",
             "step_order": 2},
        ],
    },
    {
        "name": "AD: Group Membership Audit",
        "description": "Audit membership of privileged groups",
        "category": "AD",
        "steps": [
            {"name": "Domain Admins", "step_type": "powershell", "provider": "ssh",
             "command": "Get-ADGroupMember -Identity 'Domain Admins' | Select-Object Name, SamAccountName | Format-Table -AutoSize",
             "step_order": 1},
            {"name": "Enterprise Admins", "step_type": "powershell", "provider": "ssh",
             "command": "Get-ADGroupMember -Identity 'Enterprise Admins' | Select-Object Name, SamAccountName | Format-Table -AutoSize",
             "step_order": 2, "continue_on_failure": True},
        ],
    },
    {
        "name": "AD: Computer Audit",
        "description": "Audit computer accounts (stale, enabled, disabled)",
        "category": "AD",
        "steps": [
            {"name": "Stale Computers", "step_type": "powershell", "provider": "ssh",
             "command": "Get-ADComputer -Filter {Enabled -eq $true} -Properties LastLogonTimestamp | Where-Object { $_.LastLogonTimestamp -lt (Get-Date).AddDays(-90).Ticks } | Select-Object Name, LastLogonTimestamp | Format-Table -AutoSize",
             "step_order": 1},
        ],
    },
    {
        "name": "AD: Password Reset",
        "description": "Reset a user's AD password",
        "category": "AD",
        "steps": [
            {"name": "Reset Password", "step_type": "powershell", "provider": "ssh",
             "command": "Set-ADAccountPassword -Identity '{{username}}' -NewPassword (ConvertTo-SecureString '{{new_password}}' -AsPlainText -Force) -Reset",
             "step_order": 1},
            {"name": "Force Change", "step_type": "powershell", "provider": "ssh",
             "command": "Set-ADUser -Identity '{{username}}' -ChangePasswordAtLogon $true",
             "step_order": 2},
        ],
        "variables": [
            {"name": "username", "required": True},
            {"name": "new_password", "required": True, "sensitive": True},
        ],
    },
    {
        "name": "AD: OU Structure Export",
        "description": "Export Organizational Unit structure",
        "category": "AD",
        "steps": [
            {"name": "Export OUs", "step_type": "powershell", "provider": "ssh",
             "command": "Get-ADOrganizationalUnit -Filter * -Properties DistinguishedName | Select-Object Name, DistinguishedName | Format-Table -AutoSize",
             "step_order": 1},
        ],
    },
    {
        "name": "AD: DNS Record Check",
        "description": "Verify DNS records for AD-integrated zones",
        "category": "AD",
        "steps": [
            {"name": "Check DNS", "step_type": "powershell", "provider": "ssh",
             "command": "Get-DnsServerZone | Select-Object ZoneName, ZoneType, IsAutoCreated | Format-Table -AutoSize",
             "step_order": 1},
        ],
    },
]


def seed(db: Session) -> bool:
    """Insert built-in playbooks when none exist."""
    count = db.scalar(select(func.count(Playbook.id)))
    if count and count > 0:
        return False

    now = datetime.now(UTC)

    for pb_data in PLAYBOOKS:
        pb = Playbook(
            name=pb_data["name"],
            description=pb_data.get("description"),
            category=pb_data.get("category"),
            enabled=True,
            requires_approval=False,
            auto_rollback=False,
            timeout_seconds=300,
            max_retries=1,
            created_by="seed",
            created_at=now,
            updated_at=now,
        )
        db.add(pb)
        db.flush()

        for step_data in pb_data.get("steps", []):
            step = PlaybookStep(
                playbook_id=pb.id,
                name=step_data["name"],
                step_type=step_data.get("step_type", "remote_command"),
                provider=step_data.get("provider", "ssh"),
                command=step_data.get("command", ""),
                timeout_seconds=step_data.get("timeout_seconds", 300),
                retry_count=step_data.get("retry_count", 0),
                continue_on_failure=step_data.get("continue_on_failure", False),
                step_order=step_data.get("step_order", 0),
                created_at=now,
                updated_at=now,
            )
            db.add(step)

        for var_data in pb_data.get("variables", []):
            var = PlaybookVariable(
                playbook_id=pb.id,
                name=var_data["name"],
                value=var_data.get("value"),
                variable_type=var_data.get("variable_type", "string"),
                required=var_data.get("required", False),
                sensitive=var_data.get("sensitive", False),
                default_value=var_data.get("default_value"),
                created_at=now,
                updated_at=now,
            )
            db.add(var)

    db.commit()
    return True
