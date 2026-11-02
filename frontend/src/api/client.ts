const API_BASE = import.meta.env.VITE_API_BASE || ''

type ApiOptions = RequestInit & {
  headers?: HeadersInit
}

function buildHeaders(options: ApiOptions): Headers {
  const headers = new Headers(options.headers || {})
  const hasFormBody = options.body instanceof FormData

  if (!hasFormBody && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const token = localStorage.getItem('access_token')
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  } else {
    headers.delete('Authorization')
  }

  return headers
}

export async function api(path: string, options: ApiOptions = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: buildHeaders(options),
  })

  const contentType = response.headers.get('content-type') || ''
  const body = contentType.includes('application/json')
    ? await response.json().catch(() => ({}))
    : await response.text().catch(() => '')

  if (!response.ok) {
    const message = typeof body === 'object' && body !== null
      ? body.message || body.detail || body.code
      : body
    throw new Error(message || `HTTP ${response.status}`)
  }

  return body
}
