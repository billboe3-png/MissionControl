import PageHeader from "../../components/common/PageHeader";

export default function NetworkTopologyPage() {
  return (
    <div className="p-6 space-y-4">
      <PageHeader title="Network Topology" subtitle="Live topology via agent discovery" />
      <div className="bg-gray-900 border border-gray-800 rounded p-6 text-gray-300">
        <p className="mb-2">Interactive topology demo is available while live agent data is being wired up.</p>
        <a className="text-cyan-400 underline" href="/demo/network-topology.html" target="_blank" rel="noreferrer">Open Network Topology Demo</a>
      </div>
    </div>
  );
}
