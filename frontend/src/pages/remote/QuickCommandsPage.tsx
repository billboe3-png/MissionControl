import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";

interface QuickCommand {
    label: string;
    description: string;
    command: string;
    shell: string;
    icon: string;
}

const COMMAND_CATEGORIES: { category: string; icon: string; commands: QuickCommand[] }[] = [
    {
        category: "System",
        icon: "💻",
        commands: [
            { label: "Uptime", description: "System uptime and load average", command: "uptime", shell: "bash", icon: "⏱️" },
            { label: "Hostname", description: "Show system hostname", command: "hostname", shell: "bash", icon: "🏷️" },
            { label: "Kernel Info", description: "Show kernel version and OS info", command: "uname -a", shell: "bash", icon: "🐧" },
            { label: "OS Release", description: "Show distribution info", command: "cat /etc/os-release", shell: "bash", icon: "📋" },
            { label: "Date & Time", description: "Show current date, time, and timezone", command: "date '+%Y-%m-%d %H:%M:%S %Z'", shell: "bash", icon: "🕐" },
            { label: "Who Am I", description: "Show current user", command: "whoami", shell: "bash", icon: "👤" },
        ],
    },
    {
        category: "Resources",
        icon: "📊",
        commands: [
            { label: "Disk Usage", description: "Show disk space usage", command: "df -h", shell: "bash", icon: "💾" },
            { label: "Memory", description: "Show memory usage", command: "free -h", shell: "bash", icon: "🧠" },
            { label: "Top Processes", description: "Show top 10 CPU-consuming processes", command: "ps aux --sort=-%cpu | head -11", shell: "bash", icon: "📈" },
            { label: "Top Memory", description: "Show top 10 memory-consuming processes", command: "ps aux --sort=-%mem | head -11", shell: "bash", icon: "📊" },
            { label: "Disk I/O", description: "Show disk I/O statistics", command: "iostat -x 1 1 2>/dev/null || cat /proc/diskstats", shell: "bash", icon: "💿" },
            { label: "Block Devices", description: "List block devices", command: "lsblk", shell: "bash", icon: "🗄️" },
        ],
    },
    {
        category: "Network",
        icon: "🌐",
        commands: [
            { label: "IP Addresses", description: "Show all network interfaces and IPs", command: "ip a", shell: "bash", icon: "🔗" },
            { label: "Routing Table", description: "Show routing table", command: "ip route", shell: "bash", icon: "🛤️" },
            { label: "DNS Info", description: "Show DNS resolver configuration", command: "cat /etc/resolv.conf", shell: "bash", icon: "🔍" },
            { label: "Open Ports", description: "Show listening TCP/UDP ports", command: "ss -tuln", shell: "bash", icon: "🚪" },
            { label: "Network Connections", description: "Show established connections", command: "ss -tnp state established", shell: "bash", icon: "🔗" },
            { label: "Ping Gateway", description: "Ping default gateway", command: "ip route | awk '/default/ {print $3}' | xargs -I{} ping -c 3 {}", shell: "bash", icon: "📡" },
        ],
    },
    {
        category: "Services",
        icon: "⚙️",
        commands: [
            { label: "Running Services", description: "List all running services", command: "systemctl list-units --type=service --state=running", shell: "bash", icon: "✅" },
            { label: "Failed Services", description: "Show failed services", command: "systemctl --failed", shell: "bash", icon: "❌" },
            { label: "Docker Containers", description: "Show running Docker containers", command: "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'", shell: "bash", icon: "🐳" },
            { label: "Docker Images", description: "Show Docker images", command: "docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}'", shell: "bash", icon: "📦" },
        ],
    },
    {
        category: "Logs",
        icon: "📜",
        commands: [
            { label: "Recent Syslog", description: "Show last 50 lines of syslog", command: "tail -50 /var/log/syslog 2>/dev/null || journalctl -n 50 --no-pager", shell: "bash", icon: "📋" },
            { label: "Auth Log", description: "Show recent authentication attempts", command: "tail -20 /var/log/auth.log 2>/dev/null || journalctl -u sshd -n 20 --no-pager", shell: "bash", icon: "🔐" },
            { label: "Boot Log", description: "Show last boot time", command: "last reboot | head -5", shell: "bash", icon: "🔄" },
            { label: "Journal Errors", description: "Show recent error-level journal entries", command: "journalctl -p err -n 20 --no-pager", shell: "bash", icon: "⚠️" },
        ],
    },
    {
        category: "Maintenance",
        icon: "🔧",
        commands: [
            { label: "Find Large Files", description: "Find files larger than 100MB", command: "find / -type f -size +100M -exec ls -lh {} \\; 2>/dev/null | head -20", shell: "bash", icon: "🔎" },
            { label: "Temp Files Size", description: "Show /tmp directory size", command: "du -sh /tmp 2>/dev/null", shell: "bash", icon: "🗑️" },
            { label: "Logrotate Status", description: "Check logrotate status", command: "logrotate -d /etc/logrotate.conf 2>&1 | head -10", shell: "bash", icon: "♻️" },
            { label: "Package Updates", description: "Check for available package updates", command: "apt list --upgradable 2>/dev/null || yum check-update 2>/dev/null || dnf check-update 2>/dev/null", shell: "bash", icon: "📦" },
            { label: "Update System", description: "Check and install all available updates", command: "sudo apt update && sudo apt upgrade -y 2>/dev/null || sudo yum update -y 2>/dev/null || sudo dnf update -y 2>/dev/null", shell: "bash", icon: "⬆️" },
            { label: "Cron Jobs", description: "Show current user's cron jobs", command: "crontab -l 2>/dev/null || echo 'No crontab for current user'", shell: "bash", icon: "⏰" },
        ],
    },
];

export default function QuickCommandsPage() {
    const navigate = useNavigate();

    const handleCommand = (cmd: QuickCommand) => {
        navigate(`/remote/execute?command=${encodeURIComponent(cmd.command)}&shell=${cmd.shell}`);
    };

    return (
        <>
            <PageHeader
                title="Quick Commands"
                subtitle="Common commands for remote host management"
            />
            {COMMAND_CATEGORIES.map((cat) => (
                <div key={cat.category} className="identity-overview-section">
                    <h3>{cat.icon} {cat.category}</h3>
                    <div className="quick-commands-grid">
                        {cat.commands.map((cmd) => (
                            <button
                                key={cmd.label}
                                className="quick-command-card"
                                onClick={() => handleCommand(cmd)}
                                title={cmd.command}
                            >
                                <span className="quick-command-icon">{cmd.icon}</span>
                                <span className="quick-command-label">{cmd.label}</span>
                                <span className="quick-command-desc">{cmd.description}</span>
                                <code className="quick-command-code">{cmd.command}</code>
                            </button>
                        ))}
                    </div>
                </div>
            ))}
        </>
    );
}
