import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  timeout: 10_000,
})

// Response interceptor: surface error messages clearly
api.interceptors.response.use(
  (r) => r,
  (error) => {
    const message = error.response?.data?.detail ?? error.message
    return Promise.reject(new Error(message))
  },
)
