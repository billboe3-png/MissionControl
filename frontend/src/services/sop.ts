import { apiClient } from "../utils/apiClient";

const API = "/api/v1/sop";

export interface SOPDocument {
  id: number;
  title: string;
  description: string | null;
  file_path: string | null;
  content_text: string | null;
  status: string;
  approval_status: string;
  version: string | null;
  created_by: string | null;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface SOPApproval {
  id: number;
  sop_document_id: number;
  approver_name: string;
  action: string;
  comments: string | null;
  acted_at: string;
}

export interface SOPDocumentListResponse {
  count: number;
  items: SOPDocument[];
}

export interface SOPDocumentCreateInput {
  title: string;
  description?: string;
  status?: string;
  approval_status?: string;
  version?: string;
  created_by?: string;
  file_path?: string;
}

export interface SOPDocumentUpdateInput {
  title?: string;
  description?: string;
  status?: string;
  approval_status?: string;
  version?: string;
  content_text?: string;
  approved_by?: string;
  approved_at?: string;
}

export interface SOPApprovalCreateInput {
  approver_name: string;
  action: string;
  comments?: string;
}

export const sopApi = {
  async list(): Promise<SOPDocumentListResponse> {
    return apiClient<SOPDocumentListResponse>(API);
  },

  async get(id: number): Promise<SOPDocument> {
    return apiClient<SOPDocument>(`${API}/${id}`);
  },

  async create(data: SOPDocumentCreateInput): Promise<SOPDocument> {
    return apiClient<SOPDocument>(API, {
      method: "POST",
      json: data,
    });
  },

  async update(id: number, data: SOPDocumentUpdateInput): Promise<SOPDocument> {
    return apiClient<SOPDocument>(`${API}/${id}`, {
      method: "PUT",
      json: data,
    });
  },

  async remove(id: number): Promise<void> {
    return apiClient<void>(`${API}/${id}`, {
      method: "DELETE",
    });
  },

  async approve(id: number, data: SOPApprovalCreateInput): Promise<SOPDocument> {
    return apiClient<SOPDocument>(`${API}/${id}/approvals`, {
      method: "POST",
      json: data,
    });
  },

  async extractText(id: number): Promise<{ text: string | null; source: string }> {
    return apiClient<{ text: string | null; source: string }>(`${API}/${id}/extract-text`, {
      method: "POST",
    });
  },
};
