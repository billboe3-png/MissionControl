import { NavGroup } from "../types/navigation";

export const navigation: NavGroup[] = [
    {
        label: "Dashboard",
        icon: "📊",
        items: [{ label: "Overview", path: "/", icon: "🏠" }],
        defaultOpen: true,
    },
    {
        label: "Infrastructure",
        icon: "🖥️",
        items: [
            { label: "Overview", path: "/infrastructure", icon: "📈" },
            { label: "System", path: "/infrastructure/system", icon: "💻" },
            { label: "Docker", path: "/infrastructure/docker", icon: "🐳" },
            { label: "Git", path: "/infrastructure/git", icon: "📦" },
            { label: "Health", path: "/infrastructure/health", icon: "❤️" },
        ],
    },
    {
        label: "Remote Operations",
        icon: "🔗",
        items: [
            { label: "Hosts", path: "/remote/hosts", icon: "🖥️" },
            { label: "Credentials", path: "/remote/credentials", icon: "🔑" },
            { label: "Execute", path: "/remote/execute", icon: "⚡" },
            { label: "History", path: "/remote/history", icon: "📜" },
            { label: "File Browser", path: "/remote/files", icon: "📂" },
        ],
    },
    {
        label: "Identity",
        icon: "🔐",
        items: [
            { label: "Overview", path: "/identity", icon: "📊" },
            { label: "Active Directory", path: "/identity/active-directory", icon: "🏢" },
            { label: "Microsoft 365", path: "/identity/microsoft-365", icon: "☁️" },
        ],
    },
    {
        label: "Monitoring",
        icon: "📡",
        items: [
            { label: "Overview", path: "/monitoring", icon: "📊" },
            { label: "Hosts", path: "/monitoring/hosts", icon: "🖥️" },
            { label: "Problems", path: "/monitoring/problems", icon: "🚨" },
            { label: "Triggers", path: "/monitoring/triggers", icon: "⚡" },
            { label: "Events", path: "/monitoring/events", icon: "📋" },
            { label: "Host Groups", path: "/monitoring/host-groups", icon: "📁" },
            { label: "Templates", path: "/monitoring/templates", icon: "📐" },
            { label: "Items", path: "/monitoring/items", icon: "📦" },
            { label: "Maps", path: "/monitoring/maps", icon: "🗺️" },
            { label: "Dashboards", path: "/monitoring/dashboards", icon: "📈" },
            { label: "Health", path: "/monitoring/health", icon: "❤️" },
        ],
    },
    {
        label: "Settings",
        icon: "⚙️",
        items: [
            { label: "General", path: "/settings", icon: "🔧" },
            { label: "Integrations", path: "/settings/integrations", icon: "🔌" },
            { label: "Appearance", path: "/settings/appearance", icon: "🎨" },
            { label: "About", path: "/settings/about", icon: "ℹ️" },
        ],
    },
];
