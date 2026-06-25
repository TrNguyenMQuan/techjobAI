import { api, mockDelay } from './api'

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'
const TOKEN_KEY = 'techjob_token'
const USERS_KEY = 'techjob_mock_users'

function getMockUsers() {
  const stored = localStorage.getItem(USERS_KEY)
  if (stored) return JSON.parse(stored)
  const defaults = [
    { id: '1', name: 'Nguyễn Văn A', email: 'demo@techjob.ai', password: 'demo123' },
  ]
  localStorage.setItem(USERS_KEY, JSON.stringify(defaults))
  return defaults
}

function saveMockUsers(users) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

function createToken(userId) {
  return `mock_${userId}_${Date.now()}`
}

function parseTokenUserId(token) {
  if (!token?.startsWith('mock_')) return null
  return token.split('_')[1]
}

function withoutPassword(user) {
  const safeUser = { ...user }
  delete safeUser.password
  return safeUser
}

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function clearStoredToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export function setStoredToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

/** POST /auth/login */
export async function login({ email, password }) {
  if (USE_MOCK) {
    await mockDelay(600)
    const users = getMockUsers()
    const user = users.find(u => u.email.toLowerCase() === email.toLowerCase())
    if (!user || user.password !== password) {
      throw { message: 'Email hoặc mật khẩu không đúng.' }
    }
    const token = createToken(user.id)
    setStoredToken(token)
    return { token, user: withoutPassword(user) }
  }
  const { data } = await api.post('/auth/login', { email, password })
  setStoredToken(data.token)
  return data
}

/** POST /auth/register */
export async function register({ name, email, password }) {
  if (USE_MOCK) {
    await mockDelay(700)
    const users = getMockUsers()
    if (users.some(u => u.email.toLowerCase() === email.toLowerCase())) {
      throw { message: 'Email này đã được sử dụng.' }
    }
    const user = { id: String(Date.now()), name, email, password }
    users.push(user)
    saveMockUsers(users)
    const token = createToken(user.id)
    setStoredToken(token)
    return { token, user: withoutPassword(user) }
  }
  const { data } = await api.post('/auth/register', { name, email, password })
  setStoredToken(data.token)
  return data
}

/** GET /auth/me */
export async function getCurrentUser() {
  const token = getStoredToken()
  if (!token) return null

  if (USE_MOCK) {
    await mockDelay(300)
    const userId = parseTokenUserId(token)
    if (!userId) return null
    const user = getMockUsers().find(u => u.id === userId)
    if (!user) return null
    return withoutPassword(user)
  }
  const { data } = await api.get('/auth/me')
  return data
}

export async function logout() {
  clearStoredToken()
  if (!USE_MOCK) {
    try { await api.post('/auth/logout') } catch { /* ignore */ }
  }
}
