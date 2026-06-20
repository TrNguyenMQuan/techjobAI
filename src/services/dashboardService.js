import { api, mockDelay } from './api'
import { SKILL_DATA, SALARY_BOX_DATA, TREND_DATA_3M, TREND_DATA_6M, TREND_DATA_12M } from '../data/mockData'

const USE_MOCK = true

/** FR-3.1 — Top 10 skills phổ biến */
export async function getTopSkills() {
  if (USE_MOCK) { await mockDelay(600); return SKILL_DATA }
  const { data } = await api.get('/dashboard/top-skills')
  return data
}

/** FR-3.2 — Phân phối mức lương (Junior / Mid / Senior box plot) */
export async function getSalaryDistribution() {
  if (USE_MOCK) { await mockDelay(600); return SALARY_BOX_DATA }
  const { data } = await api.get('/dashboard/salary-distribution')
  return data
}

/** FR-3.3 — Xu hướng tuyển dụng theo thời gian */
export async function getHiringTrend(range = '6M') {
  if (USE_MOCK) {
    await mockDelay(600)
    return { '3M': TREND_DATA_3M, '6M': TREND_DATA_6M, '12M': TREND_DATA_12M }[range] || TREND_DATA_6M
  }
  const { data } = await api.get('/dashboard/hiring-trend', { params: { range } })
  return data
}

/** FR-3.4 — Last-updated timestamp shown in each chart's footer */
export async function getLastUpdated() {
  if (USE_MOCK) { await mockDelay(100); return new Date().toISOString() }
  const { data } = await api.get('/dashboard/last-updated')
  return data.timestamp
}
