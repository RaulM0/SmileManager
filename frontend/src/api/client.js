let csrfToken = null

export function setCsrfToken(token) {
  csrfToken = token
}

export async function api(path, options = {}) {
  const method = options.method || 'GET'
  const headers = new Headers(options.headers || {})
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method.toUpperCase()) && csrfToken) {
    headers.set('X-CSRFToken', csrfToken)
  }
  const response = await fetch(`/api/v1/${path}`, { ...options, headers, credentials: 'include' })
  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json') ? await response.json() : null
  if (!response.ok) {
    const error = new Error(payload?.detail || 'No fue posible completar la operación.')
    error.status = response.status
    error.payload = payload
    throw error
  }
  return payload
}
