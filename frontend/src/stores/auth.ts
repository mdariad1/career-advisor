import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const role = ref<string>(localStorage.getItem('role') ?? 'user')

  const isAuthenticated = computed(() => accessToken.value !== null)

  function setTokens(access: string, refresh: string, userRole = 'user') {
    accessToken.value = access
    refreshToken.value = refresh
    role.value = userRole
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    localStorage.setItem('role', userRole)
    api.defaults.headers.common['Authorization'] = `Bearer ${access}`
  }

  function clearTokens() {
    accessToken.value = null
    refreshToken.value = null
    role.value = 'user'
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('role')
    delete api.defaults.headers.common['Authorization']
  }

  async function login(email: string, password: string) {
    const { data } = await api.post('/auth/login', { email, password })
    setTokens(data.access_token, data.refresh_token, data.role ?? 'user')
  }

  async function logout() {
    if (refreshToken.value) {
      await api.post('/auth/logout', { refresh_token: refreshToken.value }).catch(() => {})
    }
    clearTokens()
  }

  // Restore auth header on page load
  if (accessToken.value) {
    api.defaults.headers.common['Authorization'] = `Bearer ${accessToken.value}`
  }

  return { accessToken, refreshToken, role, isAuthenticated, login, logout, setTokens, clearTokens }
})
