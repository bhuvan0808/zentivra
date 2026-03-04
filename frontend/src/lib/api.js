/**
 * API Client for Zentivra Backend.
 * Wraps all fetch calls to the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

async function fetchAPI(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error ${res.status}`);
  }

  return res.json();
}

// ── Health ──────────────────────────────────────────────────────────────
export const getHealth = () => fetchAPI('/health');
export const getScheduler = () => fetchAPI('/scheduler');

// ── Sources ─────────────────────────────────────────────────────────────
export const getSources = () => fetchAPI('/api/sources/');
export const getSource = (id) => fetchAPI(`/api/sources/${id}`);
export const createSource = (data) => fetchAPI('/api/sources/', { method: 'POST', body: JSON.stringify(data) });
export const updateSource = (id, data) => fetchAPI(`/api/sources/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteSource = (id) => fetchAPI(`/api/sources/${id}`, { method: 'DELETE' });
export const toggleSource = (id, enabled) => fetchAPI(`/api/sources/${id}`, { method: 'PUT', body: JSON.stringify({ enabled }) });

// ── Runs ────────────────────────────────────────────────────────────────
export const getRuns = (limit = 20) => fetchAPI(`/api/runs/?limit=${limit}`);
export const getRun = (id) => fetchAPI(`/api/runs/${id}`);
export const triggerRun = () => fetchAPI('/api/runs/trigger', { method: 'POST' });

// ── Findings ────────────────────────────────────────────────────────────
export const getFindings = (params = {}) => {
  const qs = new URLSearchParams();
  if (params.category) qs.set('category', params.category);
  if (params.search) qs.set('search', params.search);
  if (params.min_impact) qs.set('min_impact', params.min_impact);
  if (params.limit) qs.set('limit', params.limit);
  return fetchAPI(`/api/findings/?${qs.toString()}`);
};
export const getFinding = (id) => fetchAPI(`/api/findings/${id}`);
export const getFindingStats = () => fetchAPI('/api/findings/stats');

// ── Digests ─────────────────────────────────────────────────────────────
export const getDigests = (limit = 20) => fetchAPI(`/api/digests/?limit=${limit}`);
export const getDigest = (id) => fetchAPI(`/api/digests/${id}`);
export const getDigestPDFUrl = (id) => `${API_BASE}/api/digests/${id}/pdf`;
