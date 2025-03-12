const API_BASE = window.ENV?.API_BASE || "";

export default {
  endpoints: {
    stats: `${API_BASE}/processing/stats`,
    analyzer: (endpoint, index) => `${API_BASE}/analyzer/${endpoint}?index=${index}`,
    anomalies: (type) => `${API_BASE}/anomaly/anomalies?anomaly_type=${type}`
  }
};