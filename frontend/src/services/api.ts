/**
 * API client with JWT interceptor for the CRM backend.
 */
import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
    baseURL: API_BASE,
    headers: { 'Content-Type': 'application/json' },
});

// ---------------------------------------------------------------------------
// JWT interceptor — attach token to every request
// ---------------------------------------------------------------------------
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// ---------------------------------------------------------------------------
// Response interceptor — auto-refresh on 401
// ---------------------------------------------------------------------------
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
                try {
                    const { data } = await axios.post(`${API_BASE}/auth/refresh`, {
                        refresh_token: refreshToken,
                    });
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('refresh_token', data.refresh_token);
                    originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
                    return api(originalRequest);
                } catch {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    window.location.href = '/login';
                }
            }
        }
        return Promise.reject(error);
    }
);

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export const authApi = {
    register: (data: { email: string; password: string; first_name: string; last_name: string; tenant_slug: string }) =>
        api.post('/auth/register', data),
    login: (data: { email: string; password: string }) =>
        api.post('/auth/login', data),
    me: () => api.get('/auth/me'),
    createApiKey: (data: { label: string; expires_in_days?: number }) =>
        api.post('/auth/api-keys', data),
    listApiKeys: () => api.get('/auth/api-keys'),
    deleteApiKey: (id: string) => api.delete(`/auth/api-keys/${id}`),
};

// ---------------------------------------------------------------------------
// Contacts
// ---------------------------------------------------------------------------
export const contactsApi = {
    list: (params?: { page?: number; per_page?: number; search?: string; status?: string }) =>
        api.get('/contacts', { params }),
    get: (id: string) => api.get(`/contacts/${id}`),
    create: (data: any) => api.post('/contacts', data),
    update: (id: string, data: any) => api.patch(`/contacts/${id}`, data),
    delete: (id: string) => api.delete(`/contacts/${id}`),
};

// ---------------------------------------------------------------------------
// Companies
// ---------------------------------------------------------------------------
export const companiesApi = {
    list: () => api.get('/companies'),
    contacts: (companyId: string) => api.get(`/companies/${companyId}/contacts`),
    create: (data: any) => api.post('/companies', data),
    update: (id: string, data: any) => api.patch(`/companies/${id}`, data),
    delete: (id: string) => api.delete(`/companies/${id}`),
};

// ---------------------------------------------------------------------------
// Deals
// ---------------------------------------------------------------------------
export const dealsApi = {
    list: (params?: { page?: number; per_page?: number; stage_id?: string }) =>
        api.get('/deals', { params }),
    get: (id: string) => api.get(`/deals/${id}`),
    create: (data: any) => api.post('/deals', data),
    update: (id: string, data: any) => api.patch(`/deals/${id}`, data),
    delete: (id: string) => api.delete(`/deals/${id}`),
    pipelineStats: () => api.get('/deals/stats/pipeline'),
};

// ---------------------------------------------------------------------------
// Pipeline Stages
// ---------------------------------------------------------------------------
export const stagesApi = {
    list: () => api.get('/pipeline-stages'),
};

// ---------------------------------------------------------------------------
// Activities
// ---------------------------------------------------------------------------
export const activitiesApi = {
    list: (params?: { page?: number; per_page?: number; contact_id?: string; deal_id?: string; type?: string }) =>
        api.get('/activities', { params }),
    timeline: (contactId: string) => api.get(`/activities/timeline/${contactId}`),
    create: (data: any) => api.post('/activities', data),
    update: (id: string, data: any) => api.patch(`/activities/${id}`, data),
    delete: (id: string) => api.delete(`/activities/${id}`),
};

// ---------------------------------------------------------------------------
// Reports
// ---------------------------------------------------------------------------
export const reportsApi = {
    pipeline: () => api.get('/reports/pipeline'),
    forecast: () => api.get('/reports/forecast'),
    activitySummary: (days?: number) => api.get('/reports/activity-summary', { params: { days } }),
};

// ---------------------------------------------------------------------------
// Draft Emails
// ---------------------------------------------------------------------------
export const draftEmailsApi = {
    list: (params?: { status?: string; contact_id?: string }) =>
        api.get('/draft-emails', { params }),
    update: (id: string, data: { subject?: string; body?: string; status?: string }) =>
        api.patch(`/draft-emails/${id}`, data),
    delete: (id: string) => api.delete(`/draft-emails/${id}`),
    /** Approve a draft and trigger the n8n send webhook */
    send: (id: string) => api.post(`/draft-emails/${id}/send`),
};

// ---------------------------------------------------------------------------
// Customization
// ---------------------------------------------------------------------------
export const customizationApi = {
    getFields: (entityType?: string) => api.get('/customization/fields', { params: { entity_type: entityType } }),
    createField: (data: any) => api.post('/customization/fields', data),
    deleteField: (id: string) => api.delete(`/customization/fields/${id}`),
    getSettings: () => api.get('/customization/settings'),
    updateSettings: (settings: any) => api.patch('/customization/settings', { settings }),
    getWebhooks: () => api.get('/customization/webhooks'),
    createWebhook: (data: any) => api.post('/customization/webhooks', data),
    deleteWebhook: (id: string) => api.delete(`/customization/webhooks/${id}`),
};

export default api;
