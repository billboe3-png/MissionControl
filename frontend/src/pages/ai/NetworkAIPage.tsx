import { useState } from "react";
import { networkAI } from "../../services/networkAI";

export default function NetworkAIPage() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<string | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [agentId, setAgentId] = useState<number>(1);

  const handleAsk = async () => {
    const q = question.trim();
    if (!q) return;
    setLoading(true);
    setAnswer(null);
    setConfidence(null);
    setSources([]);
    setError(null);
    try {
      const result = await networkAI.ask(agentId, q);
      setAnswer(result.answer);
      setConfidence(result.confidence);
      setSources(result.sources || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">🧠 Network AI Assistant</h1>
      <p className="text-gray-400 mb-4">
        Ask natural-language questions about your network. The server-side assistant uses collected inventory to answer.
      </p>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 mb-4">
        <label className="block text-sm text-gray-400 mb-1">Agent</label>
        <select
          value={agentId}
          onChange={(e) => setAgentId(Number(e.target.value))}
          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
        >
          <option value={1}>CORHQROBERTB</option>
        </select>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 mb-4">
        <label className="block text-sm text-gray-400 mb-1">Your question</label>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Example: Why can't I reach the Veeam server?"
          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white h-28"
        />
        <div className="mt-3 flex gap-2">
          <button
            onClick={handleAsk}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded"
          >
            {loading ? "Thinking..." : "Ask"}
          </button>
          <button
            onClick={() => {
              setQuestion("Why can't I reach the Veeam server?");
            }}
            className="bg-gray-800 hover:bg-gray-700 text-gray-200 px-4 py-2 rounded border border-gray-700"
          >
            Try example
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/40 border border-red-700 text-red-200 rounded-lg p-3 mb-4">
          {error}
        </div>
      )}

      {answer && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">Answer</h2>
            {confidence && (
              <span className="text-xs bg-gray-800 border border-gray-700 rounded px-2 py-1 text-gray-300">
                confidence: {confidence}
              </span>
            )}
          </div>
          <p className="whitespace-pre-wrap text-gray-100">{answer}</p>
          {sources.length > 0 && (
            <div className="mt-3 text-xs text-gray-500">
              sources: {sources.join(", ")}
            </div>
          )}
        </div>
      )}

      <div className="text-xs text-gray-500">
        Responses are generated from server-side inventory and assistant context. No direct connections are made from the cloud to your LAN.
      </div>
    </div>
  );
}
