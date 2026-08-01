import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { api } from "../../services/api";

const DISPLAY_NAMES: Record<string, string> = {
  postgres: "PostgreSQL",
  redis: "Redis",
  event_bus: "Event Bus",
  dashboard: "Dashboard Aggregator",
  scheduler: "Scheduler",
  automation: "Automation Engine",
  plugins: "Plugin Loader",
  heartbeat_service: "Heartbeat Service",
  agent_state_engine: "Fleet State Engine",
  ai: "AI Service",
};

interface SubsystemCheck {
  component: string;
  status: string;
  latency_ms: number;
  last_check: string;
  details?: string;
}

export default function HealthPage() {
  const [subsystems, setSubsystems] = useState<Record<string, SubsystemCheck>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.getSubsystems();
        setSubsystems(data.subsystems ?? {});
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load");
      }
    };
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, []);

  if (error) return <div className="error-banner">{error}</div>;

  const entries = Object.entries(subsystems).filter(([k]) => k !== "disk_space" && k !== "agents");

  return (
    <>
      <PageHeader title="Health" subtitle="Live system health checks" />
      <div className="health-checks">
        {entries.map(([key, check]) => (
          <div key={key} className="health-check-item">
            <span className="health-check-label">{DISPLAY_NAMES[key] ?? key}</span>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span className="health-check-latency">{check.latency_ms.toFixed(1)}ms</span>
              <StatusBadge
                status={
                  check.status === "ok" ? "healthy" :
                  check.status === "warning" ? "warning" :
                  "error"
                }
                label={check.status}
              />
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
