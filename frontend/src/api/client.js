import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:6000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Health
  health: () => apiClient.get('/health'),
  
  // Modules
  getModules: () => apiClient.get('/api/v1/modules'),
  
  // Scans
  createScan: (data) => apiClient.post('/api/v1/scans', data),
  getScans: (params) => apiClient.get('/api/v1/scans', { params }),
  getScan: (id) => apiClient.get(`/api/v1/scans/${id}`),
  getScanGraph: (id) => apiClient.get(`/api/v1/scans/${id}/graph`),
  
  // Templates
  getTemplates: (params) => apiClient.get('/api/v1/templates', { params }),
  createTemplate: (data) => apiClient.post('/api/v1/templates', data),
  getTemplate: (id) => apiClient.get(`/api/v1/templates/${id}`),
  deleteTemplate: (id) => apiClient.delete(`/api/v1/templates/${id}`),
  
  // Export
  exportJSON: (id) => apiClient.get(`/api/v1/export/${id}/json`, { responseType: 'blob' }),
  exportCSV: (id, type) => apiClient.get(`/api/v1/export/${id}/csv?export_type=${type}`, { responseType: 'blob' }),
  exportGraphML: (id) => apiClient.get(`/api/v1/export/${id}/graphml`, { responseType: 'blob' }),
};

export default apiClient;
