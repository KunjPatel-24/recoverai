// Single place for API calls. Vite proxies /api to the FastAPI backend.
export const API_BASE = '/api'

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
