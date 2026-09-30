/**
 * IntentPay Frontend API Client Service
 * Interacts with backend FastAPI endpoints via Vite dev proxy (/api).
 */

const BASE_URL = '/api';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  try {
    const response = await fetch(url, { ...options, headers });
    const data = await response.json();

    if (!response.ok) {
      const errorMsg = data?.error?.message || `HTTP ${response.status}: Request failed`;
      const err = new Error(errorMsg);
      err.status = response.status;
      err.data = data;
      throw err;
    }
    return data;
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new Error('Backend offline. Please ensure backend server is running on port 8000.');
    }
    throw err;
  }
}

export const api = {
  // System & User
  getHealth: () => request('/health'),
  getCurrentUser: () => request('/users/me'),
  resetDemoData: () => request('/dev/reset', { method: 'POST' }),

  // Dashboard & Analytics
  getDashboard: () => request('/dashboard'),
  getSpendingAnalytics: () => request('/analytics/spending'),
  getBehaviorAnalytics: () => request('/analytics/behavior'),

  // Intents
  parseIntent: (text) => request('/intents/parse', { method: 'POST', body: JSON.stringify({ text }) }),
  createIntent: (intentData) => request('/intents', { method: 'POST', body: JSON.stringify({ ...intentData, confirmed: true }) }),
  getIntents: () => request('/intents'),
  getIntent: (id) => request(`/intents/${id}`),
  updateIntent: (id, data) => request(`/intents/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteIntent: (id) => request(`/intents/${id}`, { method: 'DELETE' }),
  pauseIntent: (id) => request(`/intents/${id}/pause`, { method: 'POST' }),
  resumeIntent: (id) => request(`/intents/${id}/resume`, { method: 'POST' }),

  // Policies
  parsePolicy: (text) => request('/policies/parse', { method: 'POST', body: JSON.stringify({ text }) }),
  createPolicy: (policyData) => request('/policies', { method: 'POST', body: JSON.stringify({ ...policyData, confirmed: true }) }),
  getPolicies: () => request('/policies'),
  getPolicy: (id) => request(`/policies/${id}`),
  updatePolicy: (id, data) => request(`/policies/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePolicy: (id) => request(`/policies/${id}`, { method: 'DELETE' }),

  // Payments & Simulation
  analyzePayment: (paymentData) => request('/payments/analyze', { method: 'POST', body: JSON.stringify(paymentData) }),
  simulatePayment: (paymentData) => request('/payments/simulate', { method: 'POST', body: JSON.stringify(paymentData) }),
  confirmPayment: (id) => request(`/payments/${id}/confirm`, { method: 'POST' }),
  rejectPayment: (id) => request(`/payments/${id}/reject`, { method: 'POST' }),
  getPayments: () => request('/payments'),
  getPaymentTrace: (id) => request(`/payments/${id}/trace`),

  // Conflicts & Suggestions
  getConflicts: () => request('/conflicts'),
  getSuggestions: () => request('/suggestions'),
  dismissSuggestion: (id) => request(`/suggestions/${id}/dismiss`, { method: 'POST' }),

  // Simulator tools
  getPaymentImpact: (amount) => request('/simulator/payment-impact', { method: 'POST', body: JSON.stringify({ amount }) }),
  simulateWhatIf: (scenarioData) => request('/simulator/what-if', { method: 'POST', body: JSON.stringify(scenarioData) }),
};
