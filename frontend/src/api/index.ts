import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  timeout: 15_000,
})

// ── Token refresh logic ───────────────────────────────────────────────────────

let isRefreshing = false
let queue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = []

function flushQueue(err: unknown, token: string | null) {
  queue.forEach(({ resolve, reject }) => (err ? reject(err) : resolve(token!)))
  queue = []
}

function clearSession() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('role')
  delete api.defaults.headers.common['Authorization']
}

// ── Interceptors ──────────────────────────────────────────────────────────────

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config

    // Only attempt refresh on 401, and only once per request
    if (error.response?.status === 401 && !original._retry) {
      const refreshToken = localStorage.getItem('refresh_token')

      if (!refreshToken) {
        clearSession()
        window.location.href = '/login'
        return Promise.reject(new Error('Session expired — please log in again'))
      }

      // If a refresh is already in flight, queue this request until it resolves
      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          queue.push({ resolve, reject })
        })
          .then((token) => {
            original.headers['Authorization'] = `Bearer ${token}`
            return api(original)
          })
          .catch(() => Promise.reject(new Error('Session expired — please log in again')))
      }

      original._retry = true
      isRefreshing = true

      try {
        const { data } = await axios.post('/api/auth/refresh', { refresh_token: refreshToken })
        const newAccess: string = data.access_token
        const newRefresh: string = data.refresh_token

        localStorage.setItem('access_token', newAccess)
        localStorage.setItem('refresh_token', newRefresh)
        api.defaults.headers.common['Authorization'] = `Bearer ${newAccess}`

        flushQueue(null, newAccess)
        original.headers['Authorization'] = `Bearer ${newAccess}`
        return api(original)
      } catch (refreshErr) {
        flushQueue(refreshErr, null)
        clearSession()
        window.location.href = '/login'
        return Promise.reject(new Error('Session expired — please log in again'))
      } finally {
        isRefreshing = false
      }
    }

    // Surface backend error messages for all other errors
    const message = error.response?.data?.detail ?? error.message
    return Promise.reject(new Error(message))
  },
)
