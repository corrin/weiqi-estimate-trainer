const API_BASE = '/api'

function getToken() {
  return localStorage.getItem('token')
}

export async function api(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  let res
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  } catch (e) {
    console.error(`API fetch failed: ${path}`, e)
    throw e
  }

  if (res.status === 401) {
    console.error(`API 401: ${path}`)
    localStorage.removeItem('token')
    localStorage.removeItem('email')
    localStorage.removeItem('name')
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const err = await res.json().catch(() => {
      console.error(`API ${res.status} (non-JSON): ${path}`)
      return { detail: `Request failed (${res.status})` }
    })
    console.error(`API ${res.status}: ${path}`, err.detail)
    throw new Error(err.detail || `Request failed (${res.status})`)
  }

  return res.json()
}
