import { apiClient } from "../utils/apiClient";

const API = "/api/v1/ai";

export interface AIHealthScore {
    score: number;
    grade: string;
    factors: Record<string, number>;
    breakdown: AIHealthBreakdownItem[];
    timestamp: string;
}

export interface AIHealthBreakdownItem {
    source: string;
    score: number;
    status: string;
    details: string;
}

export interface AIIncident {
    source: string;
    host_name: string;
    message: string;
    criticality: string;
    business_impact: string;
    priority: string;
    confidence: AIConfidence;
    reasoning: string;
    suggested_actions: string[];
}

export interface AIConfidence {
    score: number;
    level: string;
    factors: Record<string, number>;
}

export interface AIRecommendation {
    id: string;
    action: string;
    template_key: string;
    category: string;
    confidence: AIConfidence;
    risk: string;
    reason: string;
    estimated_impact: string;
    explanation: string;
    requires_approval: boolean;
}

export interface AICorrelationGroup {
    group_id: string;
    host_name: string;
    alert_count: number;
    sources: string[];
    max_severity: string;
    alert_ids: string[];
    correlation_type: string;
}

export interface AICorrelationSummary {
    total_alerts: number;
    total_groups: number;
    total_duplicates: number;
    total_root_events: number;
    total_cascading: number;
    sources: string[];
    severity_distribution: Record<string, number>;
    timestamp: string;
}

export interface AICorrelationResult {
    groups: AICorrelationGroup[];
    duplicates: unknown[];
    root_events: unknown[];
    cascading_failures: unknown[];
    summary: AICorrelationSummary;
}

export interface AIOverview {
    health_score: AIHealthScore;
    critical_incidents: number;
    high_incidents: number;
    correlated_alerts: number;
    recommendations: number;
    top_risks: AIRisk[];
    summary: AISummary;
    timestamp: string;
}

export interface AIRisk {
    source: string;
    host_name: string;
    message: string;
    criticality: string;
    priority: string;
    business_impact: string;
}

export interface AISummary {
    total_alerts: number;
    classified_count: number;
    critical_count: number;
    high_count: number;
    recommendation_count: number;
    health_score: number;
    correlation_groups: number;
    timestamp: string;
}

export interface AISearchResult {
    query: string;
    answer: string;
    sources: string[];
    confidence: AIConfidence;
    related_data: Record<string, unknown>;
}

export interface AIProviderInfo {
    name: string;
    type: string;
    model: string;
    offline_capable: boolean;
}

export interface AIProviderStatus {
    provider: AIProviderInfo;
    connected: boolean;
}

export const aiApi = {
    async getOverview(): Promise<AIOverview> {
        return apiClient<AIOverview>(`${API}/overview`);
    },

    async getIncidents(): Promise<{
        incidents: AIIncident[];
        summary: AISummary;
        top_risks: AIRisk[];
    }> {
        return apiClient(`${API}/incidents`);
    },

    async getRecommendations(): Promise<{
        recommendations: AIRecommendation[];
        total: number;
        by_risk: Record<string, number>;
        timestamp: string;
    }> {
        return apiClient(`${API}/recommendations`);
    },

    async getCorrelations(): Promise<AICorrelationResult> {
        return apiClient<AICorrelationResult>(`${API}/correlations`);
    },

    async getHealthScore(): Promise<AIHealthScore> {
        return apiClient<AIHealthScore>(`${API}/health-score`);
    },

    async search(query: string): Promise<AISearchResult> {
        return apiClient<AISearchResult>(`${API}/search`, {
            method: "POST",
            json: { query },
        });
    },

    async getProviderStatus(): Promise<AIProviderStatus> {
        return apiClient<AIProviderStatus>(`${API}/provider/status`);
    },

    async testProvider(): Promise<{
        success: boolean;
        message: string | null;
        error: string | null;
        provider: AIProviderInfo | null;
    }> {
        return apiClient(`${API}/provider/test`, {
            method: "POST",
        });
    },
};
