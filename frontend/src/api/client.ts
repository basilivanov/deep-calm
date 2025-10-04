import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor для обработки ошибок
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Types
export interface Campaign {
  id: string;
  title: string;
  sku: string;
  budget_rub: number;
  target_cac_rub: number;
  target_roas: number;
  channels: string[];
  status: 'draft' | 'active' | 'paused' | 'archived';
  ab_test_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateCampaignRequest {
  title: string;
  sku: string;
  budget_rub: number;
  target_cac_rub: number;
  target_roas: number;
  channels: string[];
  ab_test_enabled: boolean;
}

export interface DashboardSummary {
  total_campaigns: number;
  active_campaigns: number;
  paused_campaigns: number;
  total_budget_rub: number;
  total_spent_rub: number;
  budget_utilization: number;
  total_leads: number;
  total_conversions: number;
  total_revenue_rub: number;
  avg_cac_rub: number | null;
  avg_roas: number | null;
  top_performing_campaign: {
    campaign_id: string;
    campaign_title: string;
    roas: number;
  } | null;
}

// API methods
export const campaignsApi = {
  list: (params?: { page?: number; page_size?: number }) =>
    apiClient.get<{ items: Campaign[]; total: number; page: number; page_size: number }>('/campaigns', { params }),

  get: (id: string) =>
    apiClient.get<Campaign>(`/campaigns/${id}`),

  create: (data: CreateCampaignRequest) =>
    apiClient.post<Campaign>('/campaigns', data),

  update: (id: string, data: Partial<CreateCampaignRequest>) =>
    apiClient.patch<Campaign>(`/campaigns/${id}`, data),

  delete: (id: string) =>
    apiClient.delete(`/campaigns/${id}`),

  activate: (id: string) =>
    apiClient.post<Campaign>(`/campaigns/${id}/activate`),

  pause: (id: string) =>
    apiClient.post<Campaign>(`/campaigns/${id}/pause`),
};

export const analyticsApi = {
  dashboard: (params?: { start_date?: string; end_date?: string }) =>
    apiClient.get<DashboardSummary>('/analytics/dashboard', { params }),

  campaignMetrics: (id: string, params?: { start_date?: string; end_date?: string }) =>
    apiClient.get(`/analytics/campaigns/${id}`, { params }),
};

// Publishing API
export const publishingApi = {
  publish: (campaignId: string) =>
    apiClient.post(`/publishing/publish`, { campaign_id: campaignId }),

  status: (campaignId: string) =>
    apiClient.get(`/publishing/status/${campaignId}`),

  pause: (campaignId: string) =>
    apiClient.post(`/publishing/pause/${campaignId}`),
};

// Integrations API
export const integrationsApi = {
  list: () =>
    apiClient.get('/integrations'),

  connect: (type: string, token: string) =>
    apiClient.post(`/integrations/${type}/connect`, { token }),

  disconnect: (type: string) =>
    apiClient.post(`/integrations/${type}/disconnect`),

  sync: (type: string) =>
    apiClient.post(`/integrations/${type}/sync`),

  status: (type: string) =>
    apiClient.get(`/integrations/${type}/status`),
};
