import { useState, useEffect, useCallback } from 'react'
import { RefreshCw } from 'lucide-react'
import { SectionHeader, Skeleton, Card } from '../components/ui'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line, Legend, Cell,
  PieChart, Pie,
} from 'recharts'
import { api } from '../services/api'

// ─── Colors ──────────────────────────────────────────────────────────────────
const LEVEL_COLORS = ['#F59E0B', '#F59E0B', '#F97316', '#F97316', '#8B5CF6']
const DONUT_COLORS = ['#3B82F6', '#60A5FA', '#93C5FD', '#6366F1', '#A78BFA']
const TREND_COLORS = ['#3B82F6', '#F59E0B', '#10B981', '#EF4444', '#8B5CF6']
const SKILL_BAR_COLOR = '#818CF8'

// ─── Chart Card ──────────────────────────────────────────────────────────────
function ChartCard({ title, children, loading, className = '' }) {
  return (
    <Card className={`p-5 flex flex-col gap-4 ${className}`}>
      <h3 className="text-base font-semibold text-text-primary">{title}</h3>
      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-32 w-full mt-2" />
        </div>
      ) : children}
    </Card>
  )
}

// ─── Stat Card ───────────────────────────────────────────────────────────────
function StatCard({ label, value, loading }) {
  return (
    <Card className="p-5">
      <p className="text-xs text-text-secondary mb-2">{label}</p>
      {loading
        ? <Skeleton className="h-8 w-24" />
        : <p className="text-3xl font-bold text-text-primary">{value}</p>
      }
    </Card>
  )
}

// ─── Custom Tooltip ──────────────────────────────────────────────────────────
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white rounded-lg shadow-modal border border-gray-100 px-3 py-2 text-xs">
      {label && <p className="font-semibold text-text-primary mb-1">{label}</p>}
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color || p.fill }} />
          <span className="text-text-secondary">{p.name}:</span>
          <span className="font-semibold text-text-primary">{p.value}</span>
        </div>
      ))}
    </div>
  )
}

// ─── Donut label ─────────────────────────────────────────────────────────────
function renderDonutLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent, name }) {
  const RADIAN = Math.PI / 180
  const radius = outerRadius + 20
  const x = cx + radius * Math.cos(-midAngle * RADIAN)
  const y = cy + radius * Math.sin(-midAngle * RADIAN)
  if (percent < 0.04) return null
  return (
    <text x={x} y={y} fill="#6B7280" textAnchor={x > cx ? 'start' : 'end'}
      dominantBaseline="central" fontSize={11}>
      {name} {(percent * 100).toFixed(1)}%
    </text>
  )
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats]     = useState({})
  const [levels, setLevels]   = useState([])
  const [cities, setCities]   = useState([])
  const [skills, setSkills]   = useState([])
  const [trends, setTrends]   = useState([])

  const fetchAll = useCallback(async () => {
    setLoading(true)
    try {
      const [sRes, lRes, cRes, skRes, tRes] = await Promise.all([
        api.get('/stats'),
        api.get('/jobs-by-level'),
        api.get('/locations'),
        api.get('/top-skills', { params: { limit: 15 } }),
        api.get('/skill-trends'),
      ])
      setStats(sRes.data)
      setLevels(lRes.data.data || [])

      // Process cities: top 3 + others
      const rawCities = cRes.data.data || []
      const top3 = rawCities.slice(0, 3)
      const othersCount = rawCities.slice(3).reduce((s, c) => s + c.job_count, 0)
      if (othersCount > 0) top3.push({ city_name_vi: 'Khác', job_count: othersCount })
      setCities(top3)

      setSkills(skRes.data.data || [])

      // Process trends: pivot {month, skill_name, job_count} → [{month, Skill1, Skill2, ...}]
      const rawTrends = tRes.data.data || []
      const monthMap = {}
      const skillNames = new Set()
      rawTrends.forEach(r => {
        skillNames.add(r.skill_name)
        if (!monthMap[r.month]) monthMap[r.month] = { month: r.month }
        monthMap[r.month][r.skill_name] = r.job_count
      })
      setTrends({ data: Object.values(monthMap).sort((a, b) => a.month.localeCompare(b.month)), skills: [...skillNames] })
    } catch (err) {
      console.error('Dashboard fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchAll() }, [fetchAll])

  const totalCityJobs = cities.reduce((s, c) => s + c.job_count, 0)

  return (
    <div className="space-y-6 animate-fade-in">
      <SectionHeader
        title="Dashboard"
        subtitle="Thống kê thị trường IT — Dữ liệu thật từ VietnamWorks"
        action={
          <button onClick={fetchAll}
            className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors">
            <RefreshCw size={13} /> Làm mới
          </button>
        }
      />

      {/* ── KPI Row ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Tổng tin tuyển dụng IT" loading={loading}
          value={stats.total_jobs?.toLocaleString() || '—'} />
        <StatCard label="Tuần gần nhất" loading={loading}
          value={new Date().toLocaleDateString('vi-VN', { month: 'long', day: 'numeric', year: 'numeric' })} />
        <StatCard label="IT Job Market Skills" loading={loading}
          value={stats.total_skills?.toLocaleString() || '—'} />
        <StatCard label="Số nhà tuyển dụng" loading={loading}
          value={stats.total_companies?.toLocaleString() || '—'} />
      </div>

      {/* ── Row 1: Jobs by Level + Location Donut ──────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Jobs by Level — horizontal bar */}
        <ChartCard title="Phân bổ việc làm theo Cấp bậc" loading={loading}>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={levels} layout="vertical"
              margin={{ top: 0, right: 50, left: 10, bottom: 0 }} barCategoryGap="20%">
              <CartesianGrid horizontal={false} stroke="#F3F4F6" />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="level_name_vi"
                tick={{ fontSize: 12, fill: '#6B7280' }} tickLine={false} axisLine={false} width={140} />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: '#F8F7FF' }} />
              <Bar dataKey="job_count" name="Jobs Count" radius={[0, 4, 4, 0]} maxBarSize={20}
                label={{ position: 'right', fontSize: 11, fill: '#374151', formatter: v => v.toLocaleString() }}>
                {levels.map((_, i) => (
                  <Cell key={i} fill={LEVEL_COLORS[i % LEVEL_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Location Donut */}
        <ChartCard title="Phân bổ việc làm theo Thành phố" loading={loading}>
          <div className="flex items-center gap-4">
            <ResponsiveContainer width="60%" height={220}>
              <PieChart>
                <Pie data={cities} dataKey="job_count" nameKey="city_name_vi"
                  cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                  label={renderDonutLabel} labelLine={false}>
                  {cities.map((_, i) => (
                    <Cell key={i} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
                {/* Center label */}
                <text x="50%" y="46%" textAnchor="middle" dominantBaseline="central"
                  fontSize={22} fontWeight={700} fill="#1E1B4B">
                  {totalCityJobs.toLocaleString()}
                </text>
                <text x="50%" y="58%" textAnchor="middle" dominantBaseline="central"
                  fontSize={11} fill="#9CA3AF">
                  Tổng
                </text>
              </PieChart>
            </ResponsiveContainer>
            <div className="flex flex-col gap-2 text-sm">
              {cities.map((c, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full" style={{ background: DONUT_COLORS[i % DONUT_COLORS.length] }} />
                  <span className="text-text-secondary">{c.city_name_vi}</span>
                  <span className="font-semibold text-text-primary ml-auto">
                    {totalCityJobs ? (c.job_count / totalCityJobs * 100).toFixed(1) : 0}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </ChartCard>
      </div>

      {/* ── Row 2: Top Skills + Skill Trends ──────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top 15 Skills — horizontal bar */}
        <ChartCard title="Top 15 Kỹ năng phổ biến" loading={loading}>
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={skills} layout="vertical"
              margin={{ top: 0, right: 50, left: 10, bottom: 0 }} barCategoryGap="18%">
              <CartesianGrid horizontal={false} stroke="#F3F4F6" />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="skill_name"
                tick={{ fontSize: 11, fill: '#6B7280' }} tickLine={false} axisLine={false} width={130} />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: '#F8F7FF' }} />
              <Bar dataKey="total_jobs" name="Total Jobs" fill={SKILL_BAR_COLOR}
                radius={[0, 4, 4, 0]} maxBarSize={16}
                label={{ position: 'right', fontSize: 10, fill: '#374151', formatter: v => v.toLocaleString() }} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Skill Trends — multi-line */}
        <ChartCard title="Top 5 Skill Demand Trends by Month" loading={loading}>
          {trends.data?.length > 0 ? (
            <ResponsiveContainer width="100%" height={380}>
              <LineChart data={trends.data}
                margin={{ top: 4, right: 16, left: -10, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="month"
                  tick={{ fontSize: 10, fill: '#9CA3AF', angle: -30, textAnchor: 'end' }}
                  tickLine={false} axisLine={false}
                  tickFormatter={v => {
                    const d = new Date(v)
                    return d.toLocaleDateString('vi-VN', { month: 'short', year: 'numeric' })
                  }}
                />
                <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} tickLine={false} axisLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Legend iconType="circle" iconSize={8}
                  wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
                {trends.skills?.map((skill, i) => (
                  <Line key={skill} type="monotone" dataKey={skill} name={skill}
                    stroke={TREND_COLORS[i % TREND_COLORS.length]}
                    strokeWidth={2} dot={{ r: 3 }}
                    activeDot={{ r: 5, strokeWidth: 0 }} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-text-muted py-10 text-center">Không có dữ liệu xu hướng</p>
          )}
        </ChartCard>
      </div>
    </div>
  )
}
