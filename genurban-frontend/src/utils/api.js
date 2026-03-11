// src/utils/api.js
import axios from 'axios';

const DEFAULT_BASE = 'http://localhost:8001'; // <-- matches main.py uvicorn port 8001
const BASE_URL = import.meta.env?.VITE_API_URL || DEFAULT_BASE;

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 12000,
  headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
});

async function retry(fn, attempts = 2, delayMs = 300) {
  let lastErr;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      await new Promise((r) => setTimeout(r, delayMs * Math.pow(2, i)));
    }
  }
  throw lastErr;
}

/**
 * testAPIConnection()
 * checks the backend at the routes exposed by main.py (/api/v1/health and root)
 */
export async function testAPIConnection() {
  const HEALTH_PATHS = ['/api/v1/health', '/api/v1/health/', '/api/v1/health/check', '/', '/api/v1/']; 
  for (const p of HEALTH_PATHS) {
    try {
      const res = await retry(() => api.get(p), 2, 300);
      if (res?.status >= 200 && res.status < 400) {
        return { connected: true, url: `${BASE_URL.replace(/\/$/, '')}${p}`, status: res.status };
      }
    } catch (err) {
      // try next
    }
  }
  return { connected: false, url: null, status: null, error: 'no reachable health endpoint' };
}

/* ---------------------------
   urbanAPI: methods used by UI
   Map endpoints to what main.py exposes in its root response
   --------------------------- */
export const urbanAPI = {
  /**
   * searchLocation(query)
   * Backend path: GET /api/v1/search-location?q=...
   * Expected result: array of results or { results: [...] }
   */
  async searchLocation(query) {
    try {
      const res = await retry(() => api.get('/api/v1/search-location', { params: { q: query } }), 2, 300);
      if (!res) return [];
      if (Array.isArray(res.data)) return res.data;
      return res.data.results || res.data.locations || res.data || [];
    } catch (err) {
      // Nominatim fallback for dev (optional)
      console.warn('Primary search failed:', err?.message);
      try {
        const nom = await axios.get('https://nominatim.openstreetmap.org/search', {
          params: { q: query, format: 'json', limit: 5 },
          timeout: 7000,
        });
        return (nom.data || []).map((it) => ({
          name: it.display_name,
          address: it.display_name,
          lat: parseFloat(it.lat),
          lng: parseFloat(it.lon),
        }));
      } catch (e) {
        console.error('Nominatim fallback failed:', e?.message);
        return [];
      }
    }
  },

  /**
   * analyzeUrbanMorphology({lat, lng, years})
   * Backend path: POST /api/v1/analyze-urban-morphology
   */
  async analyzeUrbanMorphology({ lat, lng, years = 5 }) {
    try {
      const res = await retry(() => api.post('/api/v1/analyze-urban-morphology', { lat, lng, years }), 2, 400);
      return res.data;
    } catch (err) {
      console.error('analyzeUrbanMorphology failed:', err?.message || err);
      throw err;
    }
  },

  /**
   * generateScenario(payload)
   * Backend path: POST /api/v1/generate/scenarios
   * (main.py registered router under /api/v1/generate — root listed /api/v1/generate/scenarios)
   */
  async generateScenario(payload) {
    try {
      const res = await retry(() => api.post('/api/v1/generate/scenarios', payload), 2, 400);
      return res.data;
    } catch (err) {
      console.error('generateScenario failed:', err?.message || err);
      throw err;
    }
  },

  async listScenarios() {
    try {
      const res = await api.get('/api/v1/scenarios');
      return res.data;
    } catch (err) {
      console.error('listScenarios failed:', err?.message || err);
      return [];
    }
  },
};

/**
 * formatUrbanData(raw) — normalize server response for UI
 */
export function formatUrbanData(raw) {
  if (!raw) return null;
  if (raw.metrics || raw.ndvi) return raw;
  if (raw.data) return raw.data;
  return {
    metrics: raw.metrics || null,
    ndvi: raw.ndvi || null,
    maps: raw.maps || raw.tiles || null,
    raw,
  };
}

export default api;
