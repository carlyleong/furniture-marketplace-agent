// API Configuration
const getApiBaseUrl = () => {
  // Check if we're in production (Cloud Run)
  if (window.location.hostname.includes('run.app')) {
    return 'https://furniture-backend-343631166788.us-central1.run.app';
  }
  
  // Local development - use relative URLs (proxy will handle)
  return '';
};

export const API_BASE_URL = getApiBaseUrl();

// Helper function to create full API URLs
export const getApiUrl = (endpoint) => {
  return `${API_BASE_URL}${endpoint}`;
};

export default {
  API_BASE_URL,
  getApiUrl
}; 