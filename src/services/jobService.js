import { api, mockDelay } from './api'
import { MOCK_JOBS } from '../data/mockData'

// Flip this to false once the real backend endpoints below exist.
const USE_MOCK = true

/**
 * FR-1 — Tầng 1: Filter & SQL truyền thống.
 * Fetch paginated job list with structured filters.
 */
export async function getJobs(filters = {}) {
  if (USE_MOCK) {
    await mockDelay(500)
    let results = [...MOCK_JOBS]
    if (filters.locations?.length) results = results.filter(j => filters.locations.includes(j.location))
    if (filters.levels?.length)    results = results.filter(j => filters.levels.includes(j.level))
    if (filters.types?.length)     results = results.filter(j => filters.types.includes(j.type))
    return { data: results, total: results.length }
  }
  const { data } = await api.get('/jobs', { params: filters })
  return data
}

/** FR-2 — Job detail */
export async function getJobById(id) {
  if (USE_MOCK) {
    await mockDelay(400)
    const job = MOCK_JOBS.find(j => j.id === id)
    if (!job) throw new Error('Job not found')
    return job
  }
  const { data } = await api.get(`/jobs/${id}`)
  return data
}

/**
 * FR-5 — Tầng 2: Semantic Search (vector similarity).
 * In production this hits a vector DB / embeddings endpoint; here we fall
 * back to simple keyword matching against title/skills.
 */
export async function searchJobsSemantic(query) {
  if (USE_MOCK) {
    await mockDelay(700)
    const q = query.toLowerCase()
    const results = MOCK_JOBS.filter(j =>
      j.title.toLowerCase().includes(q) ||
      j.skills.some(s => s.toLowerCase().includes(q))
    )
    return { data: results, matchType: 'semantic' }
  }
  const { data } = await api.get('/jobs/semantic-search', { params: { q: query } })
  return data
}

/** Related / similar jobs for the Job Detail page */
export async function getRelatedJobs(jobId, level) {
  if (USE_MOCK) {
    await mockDelay(300)
    return MOCK_JOBS.filter(j => j.id !== jobId && j.level === level).slice(0, 3)
  }
  const { data } = await api.get(`/jobs/${jobId}/related`)
  return data
}

/** Toggle bookmark state for a job (persisted server-side once backend exists) */
export async function toggleSaveJob(jobId) {
  if (USE_MOCK) {
    await mockDelay(150)
    return { jobId, saved: true }
  }
  const { data } = await api.post(`/jobs/${jobId}/save`)
  return data
}
