import { api, mockDelay } from './api'
import { MOCK_JOBS } from '../data/mockData'

// Flip this to false once the real backend endpoints below exist.
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'
const inflightRequests = new Map()

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms))

async function requestWithRetry(request, attempts = 5) {
  let lastError
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      return await request()
    } catch (error) {
      lastError = error
      const status = error.response?.status
      const retryable = !status || status === 429 || status >= 500
      if (!retryable || attempt === attempts - 1) throw error
      await delay(500 * (2 ** attempt))
    }
  }
  throw lastError
}

function dedupeRequest(key, request) {
  if (inflightRequests.has(key)) return inflightRequests.get(key)
  const promise = requestWithRetry(request).finally(() => {
    inflightRequests.delete(key)
  })
  inflightRequests.set(key, promise)
  return promise
}

function formatSalary(min, max) {
  if (min == null && max == null) return 'Thỏa thuận'

  const format = (value) => {
    const number = Number(value)
    if (!Number.isFinite(number)) return value
    if (number >= 100000) return `${(number / 1000000).toLocaleString('vi-VN')} triệu`
    return `$${number.toLocaleString('en-US')}`
  }

  if (min == null) return `Tối đa ${format(max)}`
  if (max == null) return `Từ ${format(min)}`
  return `${format(min)} – ${format(max)}`
}

export function normalizeJob(job) {
  const salaryMin = job.salaryMin ?? job.salary_min_vnd ?? job.salary_min ?? null
  const salaryMax = job.salaryMax ?? job.salary_max_vnd ?? job.salary_max ?? null
  const company = job.company ?? job.company_name ?? 'Không rõ công ty'
  const rawLocation = job.location ?? job.primary_city ?? 'Không rõ'
  const location = /hồ chí minh|ho chi minh/i.test(rawLocation) ? 'TP.HCM' : rawLocation
  const skills = Array.isArray(job.skills)
    ? job.skills
        .map(skill => typeof skill === 'string' ? skill : skill.skillName || skill.skill_name)
        .filter(Boolean)
    : typeof job.skills === 'string'
      ? job.skills.split(',').map(skill => skill.trim()).filter(Boolean)
      : []

  return {
    ...job,
    id: String(job.id ?? job.source_id ?? job.job_id),
    title: job.title,
    company,
    companyInitial: company.charAt(0).toUpperCase(),
    companyColor: '#4338CA',
    location,
    type: job.type ?? job.work_mode ?? '',
    level: job.level ?? job.job_level_vi ?? '',
    salaryMin,
    salaryMax,
    salaryRaw: salaryMin == null && salaryMax == null ? 'Thỏa thuận' : null,
    salaryDisplay: job.salaryDisplay ?? formatSalary(salaryMin, salaryMax),
    description: job.description ?? job.job_description ?? '',
    job_description: job.job_description ?? job.description ?? '',
    job_requirement: job.job_requirement ?? '',
    benefits: Array.isArray(job.benefits)
      ? job.benefits.map(b => typeof b === 'string' ? b : (b.benefitNameVI || b.benefitName || b.benefitValue || '')).filter(Boolean)
      : typeof job.benefits === 'string' ? [job.benefits] : [],
    skills,
    requiredSkills: job.requiredSkills ?? skills,
    postedDate: job.postedDate ?? (
      job.posted_date ? new Date(job.posted_date).toLocaleDateString('vi-VN') : ''
    ),
    sourceUrl: job.sourceUrl ?? job.source_url ?? '',
    saved: Boolean(job.saved),
  }
}

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
  const params = {
    page: filters.page || 1,
    size: filters.size || 20,
    keyword: filters.keyword || filters.q || '',
    salary_band: filters.salary_band || '',
    ai_estimate: filters.ai_estimate,
  }
  const { data } = await dedupeRequest(
    `jobs:${JSON.stringify(params)}`,
    () => api.get('/jobs', { params, timeout: 30000 }),
  )
  return { ...data, data: (data.data || []).map(normalizeJob) }
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
  return normalizeJob(data)
}

/**
 * FR-5 — Tầng 2: Semantic Search (vector similarity).
 * In production this hits a vector DB / embeddings endpoint; here we fall
 * back to simple keyword matching against title/skills.
 */
export async function searchJobsSemantic(query, limit = 30, aiEstimate = true) {
  if (USE_MOCK) {
    await mockDelay(700)
    const q = query.toLowerCase()
    const results = MOCK_JOBS.filter(j =>
      j.title.toLowerCase().includes(q) ||
      j.skills.some(s => s.toLowerCase().includes(q))
    )
    return { data: results, matchType: 'semantic' }
  }
  const params = { q: query, limit, ai_estimate: aiEstimate }
  const { data } = await dedupeRequest(
    `search:${JSON.stringify(params)}`,
    () => api.get('/search', { params, timeout: 90000 }),
  )
  return {
    data: (data.results || []).map(normalizeJob),
    total: data.results?.length || 0,
    matchType: 'semantic',
  }
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
