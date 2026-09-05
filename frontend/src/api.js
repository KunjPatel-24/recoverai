// Single place for API calls.
//
// Local dev: leave VITE_API_BASE unset. The base stays '/api' and the Vite dev
// server proxies it to uvicorn on :8000 (see vite.config.js), so there is no
// CORS involved and nothing to configure.
//
// Deployed: set VITE_API_BASE to the public backend origin at *build* time,
// e.g. VITE_API_BASE=https://recoverai-api.onrender.com/api
// Vite inlines import.meta.env at build time, so this must be present in the
// hosting provider's env vars before the build runs, not at runtime.
export const API_BASE = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '')

export async function getJSON(path) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`)
  return res.json()
}

export async function postJSON(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`POST ${path} -> ${res.status}`)
  return res.json()
}

export function inr(n) {
  if (n === null || n === undefined) return '₹0'
  return '₹' + Math.round(n).toLocaleString('en-IN')
}
