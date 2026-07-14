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
        const response = await fetch(`${API}/overview`);
        if (!response.ok) throw new Error("Failed to load AI overview");
        return response.json();
    },

    async getIncidents(): Promise<{
        incidents: AIIncident[];
        summary: AISummary;
        top_risks: AIRisk[];
    }> {
        const response = await fetch(`${API}/incidents`);
        if (!response.ok) throw new Error("Failed to load incidents");
        return response.json();
    },

    async getRecommendations(): Promise<{
        recommendations: AIRecommendation[];
        total: number;
        by_risk: Record<string, number>;
        timestamp: string;
    }> {
        const response = await fetch(`${API}/recommendations`);
        if (!response.ok) throw new Error("Failed to load recommendations");
        return response.json();
    },

    async getCorrelations(): Promise<AICorrelationResult> {
        const response = await fetch(`${API}/correlations`);
        if (!response.ok) throw new Error("Failed to load correlations");
        return response.json();
    },

    async getHealthScore(): Promise<AIHealthScore> {
        const response = await fetch(`${API}/health-score`);
        if (!response.ok) throw new Error("Failed to load health score");
        return response.json();
    },

    async search(query: string): Promise<AISearchResult> {
        const response = await fetch(`${API}/search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query }),
        });
        if (!response.ok) throw new Error("Search failed");
        return response.json();
    },

    async getProviderStatus(): Promise<AIProviderStatus> {
        const response = await fetch(`${API}/provider/status`);
        if (!response.ok) throw new Error("Failed to get provider status");
        return response.json();
    },

    async testProvider(): Promise<{
        success: boolean;
        message: string | null;
        error: string | null;
        provider: AIProviderInfo | null;
    }> {
        const response = await fetch(`${API}/provider/test`, {
            method: "POST",
        });
        if (!response.ok) throw new Error("Provider test failed");
        return response.json();
    },
};
