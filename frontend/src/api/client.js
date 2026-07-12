import axios from 'axios';

// Use relative URLs so Nginx proxy handles routing
const API_BASE_URL = '';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Health & Stats
  health: () => apiClient.get('/health'),
  getStats: () => apiClient.get('/api/v1/stats'),
  getSetupStatus: () => apiClient.get('/api/v1/setup/status'),
  search: (q) => apiClient.get('/api/v1/search', { params: { q } }),

  // Modules
  getModules: () => apiClient.get('/api/v1/modules'),
  suggestModules: (nodeType) => apiClient.get('/api/v1/modules/suggest', { params: { node_type: nodeType } }),

  // Cases
  getCases: (params) => apiClient.get('/api/v1/cases', { params }),
  getCase: (id) => apiClient.get(`/api/v1/cases/${id}`),
  createCase: (data) => apiClient.post('/api/v1/cases', data),
  updateCase: (id, data) => apiClient.put(`/api/v1/cases/${id}`, data),
  updateCaseStatus: (id, status) => apiClient.patch(`/api/v1/cases/${id}/status`, { status }),
  deleteCase: (id) => apiClient.delete(`/api/v1/cases/${id}`),
  getCaseScans: (caseId) => apiClient.get(`/api/v1/cases/${caseId}/scans`),
  getCaseGraph: (caseId) => apiClient.get(`/api/v1/cases/${caseId}/graph`),

  // Case Notes
  getCaseNotes: (caseId) => apiClient.get(`/api/v1/cases/${caseId}/notes`),
  createNote: (caseId, data) => apiClient.post(`/api/v1/cases/${caseId}/notes`, data),
  deleteNote: (caseId, noteId) => apiClient.delete(`/api/v1/cases/${caseId}/notes/${noteId}`),

  // Reports
  getCaseReports: (caseId) => apiClient.get(`/api/v1/cases/${caseId}/reports`),
  createReport: (caseId, data) => apiClient.post(`/api/v1/cases/${caseId}/reports`, data),
  getAllReports: (params) => apiClient.get('/api/v1/reports', { params }),
  getReport: (id) => apiClient.get(`/api/v1/reports/${id}`),
  deleteReport: (id) => apiClient.delete(`/api/v1/reports/${id}`),
  previewReport: (id) => `/api/v1/reports/${id}/preview`,
  downloadReportUrl: (id) => `/api/v1/reports/${id}/download`,

  // Scans
  createScan: (data) => apiClient.post('/api/v1/scans', data),
  getScans: (params) => apiClient.get('/api/v1/scans', { params }),
  getScan: (id) => apiClient.get(`/api/v1/scans/${id}`),
  getScanGraph: (id) => apiClient.get(`/api/v1/scans/${id}/graph`),
  getScanChildren: (id) => apiClient.get(`/api/v1/scans/${id}/children`),

  // Templates
  getTemplates: (params) => apiClient.get('/api/v1/templates', { params }),
  createTemplate: (data) => apiClient.post('/api/v1/templates', data),
  getTemplate: (id) => apiClient.get(`/api/v1/templates/${id}`),
  deleteTemplate: (id) => apiClient.delete(`/api/v1/templates/${id}`),

  // Export
  exportJSON: (id) => apiClient.get(`/api/v1/export/${id}/json`, { responseType: 'blob' }),
  exportCSV: (id, type) => apiClient.get(`/api/v1/export/${id}/csv?export_type=${type}`, { responseType: 'blob' }),
  exportGraphML: (id) => apiClient.get(`/api/v1/export/${id}/graphml`, { responseType: 'blob' }),

  // Integrations
  getIntegrations: () => apiClient.get('/api/v1/integrations'),
  getIntegration: (provider) => apiClient.get(`/api/v1/integrations/${provider}`),
  saveIntegration: (provider, data) => apiClient.put(`/api/v1/integrations/${provider}`, data),
  deleteIntegration: (provider) => apiClient.delete(`/api/v1/integrations/${provider}`),
  testIntegration: (provider) => apiClient.post(`/api/v1/integrations/${provider}/test`),
  importEnvIntegrations: () => apiClient.post('/api/v1/integrations/import-env'),

  // AI
  getAiSettings:  () => apiClient.get('/api/v1/ai/settings'),
  getAiProviders: () => apiClient.get('/api/v1/ai/providers'),
  saveAiSettings: (data) => apiClient.put('/api/v1/ai/settings', data),
  testAiSettings: () => apiClient.post('/api/v1/ai/test'),
  analyzeWithAi:  (data) => apiClient.post('/api/v1/ai/analyze', data),
};

export default apiClient;
