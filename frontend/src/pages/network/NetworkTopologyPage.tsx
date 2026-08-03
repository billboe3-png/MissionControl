import { useEffect, useRef, useState } from "react";
import CytoscapeComponent from "react-cytoscapejs";
import { Network as VisNetwork } from "vis-network/standalone";
// @ts-ignore
import DataSet from "vis-data";
import * as d3 from "d3";
import { NetworkTopologyResponse, NetworkDevice, DEMO_TOPOLOGY } from "../services/network";

type ViewMode = "cytoscape" | "vis" | "d3";

const COLORS: Record<string, string> = {
  switch: "#2563eb",
  server: "#16a34a",
  workstation: "#f59e0b",
  storage: "#7c3aed",
  unknown: "#6b7280",
};

function classify(device: NetworkDevice): string {
  const name = (device.hostname || "").toLowerCase();
  if (name.includes("switch") || name.includes("sw")) return "switch";
  if (name.includes("veeam") || name.includes("backup")) return "server";
  if (name.includes("nas") || name.includes("storage")) return "storage";
  if (name.includes("hyperv") || name.includes("vm")) return "server";
  if ((device.ip || "").startsWith("192.168.10.")) return "workstation";
  return "unknown";
}

function colorFor(device: NetworkDevice) {
  return COLORS[classify(device)] || COLORS.unknown;
}

export default function NetworkTopologyPage() {
  const [view, setView] = useState<ViewMode>("cytoscape");
  const [selected, setSelected] = useState<NetworkDevice | null>(null);
  const [topology, setTopology] = useState<NetworkTopologyResponse | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    Promise.resolve({ data: DEMO_TOPOLOGY }).then((res) => {
      if (!cancelled) {
        setTopology(res.data);
        setIsLoading(false);
      }
    }).catch((e: any) => {
      if (!cancelled) {
        setError(e?.message || "Failed to load");
        setIsLoading(false);
      }
    });
    return () => { cancelled = true; };
  }, []);

  const buildElements = () => {
    if (!topology) return { nodes: [], edges: [] };
    const nodeSet = new Set<string>();
    const nodes: any[] = [];
    const edges: any[] = [];

    const addNode = (id: string, label: string, device?: NetworkDevice) => {
      if (nodeSet.has(id)) return;
      nodeSet.add(id);
      nodes.push({
        data: {
          id,
          label,
          color: device ? { background: colorFor(device), border: "#111827" } : undefined,
        },
      });
    };

    (topology.devices || []).forEach((device: NetworkDevice) => {
      const devId = device.mac || device.ip;
      addNode(devId, device.hostname || device.ip, device);

      if (device.switch_ip) {
        addNode(device.switch_ip, device.switch_ip || "Switch");
        edges.push({
          data: {
            source: devId,
            target: device.switch_ip,
            label: device.switch_port || "",
          },
        });
      }
    });

    return { nodes, edges };
  };

  const renderCytoscape = () => {
    const elements = buildElements();
    const layout = { name: "cose" as const, animate: false, padding: 40 };
    const stylesheet = [
      {
        selector: "node",
        style: {
          label: "data(label)",
          "font-size": "12px",
          "text-valign": "center",
          "text-halign": "center",
          width: 60,
          height: 60,
          "background-color": "data(color?.background)",
          color: "#fff",
          "border-width": 2,
          "border-color": "data(color?.border)",
        },
      },
      {
        selector: "edge",
        style: {
          label: "data(label)",
          "font-size": "10px",
          "curve-style": "bezier",
          "target-arrow-shape": "triangle",
          "target-arrow-color": "#94a3b8",
          "line-color": "#94a3b8",
          width: 2,
          "text-rotation": "autorotate",
          "text-outline-color": "#ffffff",
          "text-outline-opacity": 0.6,
        },
      },
    ];
    return (
      <CytoscapeComponent
        elements={elements as any}
        layout={layout as any}
        stylesheet={stylesheet as any}
        style={{ width: "100%", height: "100%" }}
        minZoom={0.3}
        maxZoom={3}
      />
    );
  };

  const renderVis = () => {
    const ref = useRef<HTMLDivElement>(null);
    const { nodes, edges } = buildElements();

    useEffect(() => {
      if (!ref.current) return;
      ref.current.innerHTML = "";
      const container = document.createElement("div");
      container.style.width = "100%";
      container.style.height = "100%";
      ref.current.appendChild(container);

      const data = {
        nodes: new DataSet(nodes.map((n: any) => n.data)),
        edges: new DataSet(
          edges.map((e: any) => ({
            ...e.data,
            arrows: "to" as const,
            font: { align: "middle" as const, size: 10 },
          }))
        ),
      };
      const options = {
        nodes: {
          shape: "dot" as const,
          size: 18,
          font: { color: "#e5e7eb" },
          borderWidth: 2,
          color: { border: "#111827", background: "#2563eb" },
        },
        edges: {
          color: { color: "#94a3b8", highlight: "#22d3ee" },
          arrows: { to: { enabled: true, scaleFactor: 0.6 } },
          font: { color: "#e5e7eb", size: 10, strokeWidth: 3 },
          smooth: { enabled: true, type: "cubicBezier", roundness: 0.1 },
        },
        physics: { stabilization: true },
        interaction: { hover: true },
      };
      new VisNetwork(container, data, options);
    }, [nodes, edges]);

    return <div ref={ref} style={{ width: "100%", height: "100%" }} />;
  };

  const renderD3 = () => {
    const ref = useRef<HTMLDivElement>(null);
    const { nodes, edges } = buildElements();
    const nodeMap = new Map((nodes as any[]).map((n: any) => [n.data.id, n.data]));
    const width = 1200;
    const height = 800;

    useEffect(() => {
      if (!ref.current) return;
      ref.current.innerHTML = "";
      const svg = d3.select(ref.current).append("svg").attr("viewBox", [0, 0, width, height]);
      const g = svg.append("g");
      const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.2, 4]).on("zoom", (event) => g.attr("transform", event.transform));
      svg.call(zoom as any);

      const simulation = d3
        .forceSimulation(Array.from(nodeMap.values()) as any[])
        .force("link", d3.forceLink(edges.map((e: any) => e.data)).id((d: any) => d.id))
        .force("charge", d3.forceManyBody().strength(-400))
        .force("center", d3.forceCenter(width / 2, height / 2));

      const link = g.append("g").selectAll("line").data(edges).join("line").attr("stroke", "#475569").attr("stroke-width", 1.5);
      const label = g.append("g").selectAll("text").data(edges).join("text").text((d: any) => d.data.label).attr("font-size", 9).attr("fill", "#e5e7eb").attr("text-anchor", "middle");
      const node = g
        .append("g")
        .selectAll("circle")
        .data(Array.from(nodeMap.values()))
        .join("circle")
        .attr("r", 10)
        .attr("fill", (d: any) => d.color?.background || "#2563eb")
        .attr("stroke", "#111827")
        .attr("stroke-width", 2)
        .on("click", (_event: any, d: any) => {
          const dev = (topology?.devices || []).find((x: NetworkDevice) => (x.mac || x.ip) === d.id);
          if (dev) setSelected(dev);
        });

      simulation.on("tick", () => {
        link
          .attr("x1", (d: any) => d.source.x)
          .attr("y1", (d: any) => d.source.y)
          .attr("x2", (d: any) => d.target.x)
          .attr("y2", (d: any) => d.target.y);
        label
          .attr("x", (d: any) => (d.source.x + d.target.x) / 2)
          .attr("y", (d: any) => (d.source.y + d.target.y) / 2);
        node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);
      });
    }, [nodes, edges, topology?.devices]);

    return <div ref={ref} style={{ width: "100%", height: "100%" }} />;
  };

  const renderGraph = () => {
    switch (view) {
      case "cytoscape":
        return renderCytoscape();
      case "vis":
        return renderVis();
      case "d3":
        return renderD3();
      default:
        return null;
    }
  };

  if (isLoading) return <div className="p-6 text-gray-300">Loading topology...</div>;
  if (error) return <div className="p-6 text-red-400">Failed to load topology</div>;

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-100">Network Topology</h1>
          <p className="text-sm text-gray-400">
            Discovered: {topology?.discovered_at ? new Date(topology.discovered_at).toLocaleString() : "—"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={view}
            onChange={(e) => setView(e.target.value as ViewMode)}
            className="bg-gray-800 border border-gray-700 text-gray-200 rounded px-3 py-2"
          >
            <option value="cytoscape">Cytoscape</option>
            <option value="vis">Vis Network</option>
            <option value="d3">D3 Force</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded h-[600px]">{renderGraph()}</div>
        <div className="bg-gray-900 border border-gray-800 rounded p-4 space-y-3">
          <h2 className="text-gray-200 font-medium">Legend</h2>
          <div className="space-y-2">
            {Object.entries(COLORS).map(([key, value]) => (
              <div key={key} className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full" style={{ background: value }} />
                <span className="text-gray-300 text-sm capitalize">{key}</span>
              </div>
            ))}
          </div>
          <h3 className="text-gray-200 font-medium mt-4">Devices</h3>
          <div className="space-y-2 max-h-[320px] overflow-auto">
            {(topology?.devices || []).map((device: NetworkDevice) => (
              <button
                key={device.mac || device.ip}
                onClick={() => setSelected(device)}
                className={`w-full text-left border rounded px-3 py-2 ${
                  selected?.mac === device.mac || selected?.ip === device.ip
                    ? "border-cyan-500 bg-gray-800"
                    : "border-gray-800 hover:border-gray-600"
                }`}
              >
                <div className="text-gray-200 text-sm">{device.hostname || device.ip}</div>
                <div className="text-gray-500 text-xs">{device.ip} • {device.switch_port || ""}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {selected && (
        <div className="bg-gray-900 border border-gray-800 rounded p-4">
          <div className="flex items-center justify-between">
            <h3 className="text-gray-200 font-medium">Device Detail</h3>
            <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-200">Close</button>
          </div>
          <div className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
            {(Object.entries(selected) as Array<[string, any]>).map(([key, value]) => (
              <div key={key}>
                <span className="text-gray-500">{key}: </span>
                <span className="text-gray-200">{String(value ?? "")}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
