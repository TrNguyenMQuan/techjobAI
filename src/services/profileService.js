import { api, mockDelay } from './api'
import { MOCK_PROFILE } from '../data/mockData'

const USE_MOCK = true

/** FR-4 — Profile & Career Preferences */
export async function getProfile() {
  if (USE_MOCK) { await mockDelay(400); return MOCK_PROFILE }
  const { data } = await api.get('/profile')
  return data
}

export async function updateProfile(patch) {
  if (USE_MOCK) { await mockDelay(400); return { ...MOCK_PROFILE, ...patch } }
  const { data } = await api.put('/profile', patch)
  return data
}

/** Upload CV — multipart/form-data, max 10MB per the design spec */
export async function uploadCV(file) {
  if (USE_MOCK) {
    await mockDelay(900)
    return { name: file.name, size: file.size, uploadedAt: new Date().toISOString() }
  }
  const form = new FormData()
  form.append('cv', file)
  const { data } = await api.post('/profile/cv', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
