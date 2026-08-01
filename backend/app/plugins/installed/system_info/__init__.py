"""
System Information Plugin

A sample server plugin that provides a dashboard widget
showing basic system information.
"""

from app.plugins.server import ServerPluginSDK


class SystemInfoPlugin(ServerPluginSDK):
    """Server plugin that exposes system information on the dashboard."""

    async def setup(self) -> None:
        pass

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def get_dashboard_widgets(self) -> list[dict]:
        return [
            {
                "id": "system-info",
                "title": "System Information",
                "component": "SystemInfoWidget",
                "size": "medium",
                "refresh_interval": 300,
            }
        ]

    async def get_widget_data(self, widget_id: str) -> dict:
        if widget_id == "system-info":
            import platform
            return {
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "hostname": platform.node(),
            }
        return {}

    async def health_check(self) -> dict:
        return {"status": "ok", "version": self.version, "plugin": self.slug}
