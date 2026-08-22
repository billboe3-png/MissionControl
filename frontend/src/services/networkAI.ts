import { apiClient } from "../utils/apiClient";

const API = "/api/v1";

export interface EdgeAIAskResponse {
  question: string;
  answer: string;
  confidence: string;
  sources: string[];
  timestamp: string;
}

export interface NetworkAIStatusResponse {
  plugin: string;
  version: string;
  initialized: boolean;
  interactions_total: number;
}

export const networkAI = {
  async ask(agentId: number, question: string, contextPlugins: string[] = []): Promise<EdgeAIAskResponse> {
    return apiClient<EdgeAIAskResponse>(`${API}/edge/${agentId}/ai/ask`, {
      method: "POST",
      json: { question, context_plugins: contextPlugins },
    });
  },
};
