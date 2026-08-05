import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { agentsApi, Agent } from "../../services/agents";

type TopologyNode = {
  id: string;
  name: string;
  type: "server" | "proxy" | "target";
  status: "online" | "offline" | "unknown";
  children?: TopologyNode[];
  meta?: Record<string, string | number | null>;
};

export default function TopologyPage() {
  const [nodes, setNodes] = useState<TopologyNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    agentsApi
      .list()
      .then((res) => {
        if (cancelled) return;
        const serverNode: TopologyNode = {
          id: "server",
          name: "Mission Control Server",
          type: "server",
          status: "online",
          meta: {
            location: "GCE",
            ip: "34.35.177.209",
            agents: res.items?.length ?? 0,
          },
          children: [],
        };

        const proxyNodes: TopologyNode[] = (res.items ?? []).map((agent: Agent) => {
          const targets: TopologyNode[] = [];
          return {
            id: `agent-${agent.id}`,
            name: agent.name ?? `Agent ${agent.id}`,
            type: "proxy",
            status: agent.status === "online" ? "online" : "offline",
            meta: {
              agent_id: agent.id,
              last_heartbeat: agent.last_heartbeat,
              platform: agent.operating_system ?? "unknown",
              ip: agent.ip_address,
            },
            children: targets,
          };
        });

        setNodes([{ ...serverNode, children: proxyNodes }]);
        setLoading(false);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e.message);
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const renderNode = (node: TopologyNode, depth = 0) => {
    const statusColor =
      node.status === "online"
        ? "#22c55e"
        : node.status === "offline"
        ? "#ef4444"
        : "#94a3b8";

    return (
      <div
        key={node.id}
        style={{
          marginLeft: depth * 24,
          padding: "8px 12px",
          borderLeft: `2px solid ${statusColor}`,
          marginBottom: 4,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <StatusBadge
            status={node.status === "online" ? "healthy" : node.status === "offline" ? "error" : "neutral"}
            label={node.type.toUpperCase()}
          />
          <strong>{node.name}</strong>
          {node.meta?.hostname && (
            <span style={{ color: "#64748b", fontSize: 12 }}>
              ({node.meta.hostname}
              {node.meta.port ? `:${node.meta.port}` : ""})
            </span>
          )}
          {node.meta?.ip && (
            <span style={{ color: "#64748b", fontSize: 12 }}>
              [{node.meta.ip}]
            </span>
          )}
        </div>
        {node.meta?.last_heartbeat && (
          <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>
            Last heartbeat: {new Date(node.meta.last_heartbeat as string).toLocaleString()}
          </div>
        )}
        {node.children?.map((child) => renderNode(child, depth + 1))}
      </div>
    );
  };

  if (error) return <div className="error-banner">{error}</div>;
  if (loading) return <div className="loading-bar" />;

  return (
    <>
      <PageHeader
        title="Topology"
        subtitle="Server → Proxy → Target hierarchy"
      />
      <div className="topology-tree">{nodes.map((node) => renderNode(node))}</div>
    </>
  );
}
