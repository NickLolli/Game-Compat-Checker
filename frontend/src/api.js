// Thin wrapper around the FastAPI backend endpoints built in Week 4.
// Assumes the backend is running locally at this address - see
// backend/README or the main project README for how to start it.
const API_BASE = 'http://127.0.0.1:8000'

async function handleResponse(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${res.status})`)
  }
  return res.json()
}

export function searchGame(name) {
  const params = new URLSearchParams({ name })
  return fetch(`${API_BASE}/search-game?${params}`).then(handleResponse)
}

export function compareGame(appid) {
  const params = new URLSearchParams({ appid })
  return fetch(`${API_BASE}/compare?${params}`).then(handleResponse)
}

export function compareCustom(appid, specs) {
  const params = new URLSearchParams({ appid })
  return fetch(`${API_BASE}/compare-custom?${params}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(specs),
  }).then(handleResponse)
}

export function detectHardware() {
  return fetch(`${API_BASE}/detect-hardware`).then(handleResponse)
}
