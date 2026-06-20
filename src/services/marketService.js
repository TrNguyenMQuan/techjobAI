import { api, mockDelay } from './api'
import { MARKET_SALARY_DATA, EMERGING_SKILLS } from '../data/mockData'

const USE_MOCK = true

export async function getMarketOverview() {
  if (USE_MOCK) {
    await mockDelay(500)
    return {
      headline: 'State of the Market: Q3 Analysis',
      summary:
        'Nhu cầu tuyển dụng kỹ sư Mid-to-Senior tại Việt Nam đã ổn định, với mức tăng đáng kể +15% các vị trí yêu cầu AI/ML.',
    }
  }
  const { data } = await api.get('/market/overview')
  return data
}

export async function getSalaryByStack() {
  if (USE_MOCK) { await mockDelay(500); return MARKET_SALARY_DATA }
  const { data } = await api.get('/market/salary-by-stack')
  return data
}

export async function getEmergingSkills() {
  if (USE_MOCK) { await mockDelay(500); return EMERGING_SKILLS }
  const { data } = await api.get('/market/emerging-skills')
  return data
}

export async function getDemandHeatmap(scope = 'All Roles') {
  if (USE_MOCK) {
    await mockDelay(500)
    return [
      { city: 'TP.HCM', pct: 55 },
      { city: 'Hà Nội', pct: 35 },
      { city: 'Đà Nẵng', pct: 10 },
    ]
  }
  const { data } = await api.get('/market/demand-heatmap', { params: { scope } })
  return data
}
