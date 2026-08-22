import { apiClient } from "../utils/apiClient";

const API = "/api/v1/sops";

export interface SOP {
  id: number;
  company_id: number | null;
  site_id: number | null;
  title: string;
  description: string | null;
  status: string;
  current_version: string | null;
  tags: string | null;
  purpose: string | null;
  procedure: string | null;
  created_at: string;
  updated_at: string;
}

export interface SOPListResponse {
  count: number;
  items: SOP[];
}

export interface SOPCreateInput {
  title: string;
  description?: string;
  company_id?: number;
  site_id?: number;
  category_id?: number;
  owner_id?: number;
  tags?: string;
  purpose?: string;
  procedure?: string;
}

export interface SOPUpdateInput {
  title?: string;
  description?: string;
  tags?: string;
  purpose?: string;
  procedure?: string;
  change_reason?: string;
}

export interface SOPVersionResponse {
  id: number;
  sop_id: number;
  version: string;
  status: string;
  title: string;
  created_at: string;
}

export interface SOPImportRequest {
  file_path: string;
  source_name: string;
  title: string;
  description?: string;
  company_id?: number;
  site_id?: number;
  category_id?: number;
  owner_id?: number;
  tags?: string;
}

export interface SOPImportResponse {
  sop: SOP;
  source: {
    source_name: string;
    source_type: string;
    source_hash: string | null;
    imported_at: string;
    processing_error: string | null;
  };
  extracted_text: string | null;
  source_deleted: boolean;
}

export interface SOPReviewResponse {
  assessment: string;
  completeness_score: number;
  risk_level: string;
  findings: string[];
  recommendations: string[];
  evidence: string[];
  confidence: number;
}

export interface AIQueryResponse {
  query: string;
  answer: string;
  sources: string[];
  confidence: { score: number };
  related_data: Record<string, unknown>;
  suggested_actions: string[];
}

export const sopApi = {
  async list(params?: { company_id?: number; site_id?: number; status?: string; q?: string }): Promise<SOPListResponse> {
    const qs = new URLSearchParams();
    if (params?.company_id) qs.set("company_id", String(params.company_id));
    if (params?.site_id) qs.set("site_id", String(params.site_id));
    if (params?.status) qs.set("status", params.status);
    if (params?.q) qs.set("q", params.q);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return apiClient<SOPListResponse>(`${API}${suffix}`);
  },

  async get(id: number): Promise<SOP> {
    return apiClient<SOP>(`${API}/${id}`);
  },

  async create(data: SOPCreateInput): Promise<SOP> {
    return apiClient<SOP>(API, { method: "POST", json: data });
  },

  async update(id: number, data: SOPUpdateInput): Promise<SOP> {
    return apiClient<SOP>(`${API}/${id}`, { method: "PUT", json: data });
  },

  async remove(id: number): Promise<void> {
    return apiClient<void>(`${API}/${id}`, { method: "DELETE" });
  },

  async submit(id: number): Promise<SOP> {
    return apiClient<SOP>(`${API}/${id}/submit`, { method: "POST" });
  },

  async approve(id: number, comments?: string): Promise<SOP> {
    const qs = new URLSearchParams();
    if (comments) qs.set("comments", comments);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return apiClient<SOP>(`${API}/${id}/approve${suffix}`, { method: "POST" });
  },

  async reject(id: number, comments?: string): Promise<SOP> {
    const qs = new URLSearchParams();
    if (comments) qs.set("comments", comments);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return apiClient<SOP>(`${API}/${id}/reject${suffix}`, { method: "POST" });
  },

  async publish(id: number): Promise<SOP> {
    return apiClient<SOP>(`${API}/${id}/publish`, { method: "POST" });
  },

  async versions(id: number): Promise<SOPVersionResponse[]> {
    return apiClient<SOPVersionResponse[]>(`${API}/${id}/versions`);
  },

  async search(q: string, company_id?: number): Promise<SOPListResponse> {
    const qs = new URLSearchParams({ q });
    if (company_id) qs.set("company_id", String(company_id));
    return apiClient<SOPListResponse>(`${API}/search?${qs.toString()}`);
  },

  async importDocument(data: SOPImportRequest): Promise<SOPImportResponse> {
    return apiClient<SOPImportResponse>(`${API}/import`, { method: "POST", json: data });
  },

  async aiReview(id: number): Promise<SOPReviewResponse> {
    return apiClient<SOPReviewResponse>(`${API}/${id}/ai/review`, { method: "POST" });
  },

  async aiQuery(query: string, company_id?: number): Promise<AIQueryResponse> {
    const qs = new URLSearchParams({ query });
    if (company_id) qs.set("company_id", String(company_id));
    return apiClient<AIQueryResponse>(`${API}/query?${qs.toString()}`, { method: "POST" });
  },
};
