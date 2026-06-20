import axios from 'axios'

// ─────────────────────────────────────────────────────────────────────────────
// Central Axios instance. Point VITE_API_URL at your real backend when it's
// ready — every service in src/services/* is already written to call through
// here, so swapping from mock data to live data is a one-line change per
// service (see the `USE_MOCK` flag at the top of each service file).
// ─────────────────────────────────────────────────────────────────────────────
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach auth token if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('techjob_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Centralized error handling — surfaces a consistent shape to callers
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.message ||
      error.message ||
      'Đã xảy ra lỗi không xác định.'
    return Promise.reject({ ...error, message })
  }
)

// Small helper used by mock services to simulate realistic network latency
export const mockDelay = (ms = 500) => new Promise((resolve) => setTimeout(resolve, ms))

export default api
