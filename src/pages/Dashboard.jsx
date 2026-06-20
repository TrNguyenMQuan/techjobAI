import { useState, useEffect } from 'react'
import { MoreHorizontal, Clock, RefreshCw } from 'lucide-react'
import { SectionHeader, Skeleton, Card } from '../components/ui'
import { SkillBarChart, SalaryBoxPlot, TrendLineChart } from '../components/charts'
import {
  SKILL_DATA, SALARY_BOX_DATA,
  TREND_DATA_3M, TREND_DATA_6M, TREND_DATA_12M,
} from '../data/mockData'

// Timestamp badge shared
function UpdateBadge() {
  return (
    <div className="flex items-center gap-1 text-2xs text-text-muted">
      <Clock size={11} />
      Cập nhật lúc: 02:00 AM hôm nay
    </div>
  )
}

// Chart card wrapper
function ChartCard({ title, subtitle, badge, action, children, loading, footer }) {
  return (
    <Card className="p-5 flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-base font-semibold text-text-primary">{title}</h3>
          {subtitle && <p className="text-xs text-text-secondary mt-0.5">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-2">
          {badge}
          {action ?? (
            <button className="p-1 rounded hover:bg-gray-100 text-text-muted transition-colors">
              <MoreHorizontal size={16} />
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-4/6" />
          <Skeleton className="h-32 w-full mt-2" />
        </div>
      ) : (
        children
      )}

      <div className="pt-1 border-t border-gray-50">
        {footer ?? <UpdateBadge />}
      </div>
    </Card>
  )
}

// Summary stat cards at top
function StatCard({ label, value, sub, color }) {
  return (
    <Card className="p-4">
      <p className="text-xs text-text-secondary mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color || 'text-indigo'}`}>{value}</p>
      {sub && <p className="text-xs text-mint mt-1">{sub}</p>}
    </Card>
  )
}

const TREND_MAP = { '3M': TREND_DATA_3M, '6M': TREND_DATA_6M, '12M': TREND_DATA_12M }

export default function Dashboard() {
  const [loading, setLoading]       = useState(true)
  const [trendRange, setTrendRange] = useState('6M')

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 1200)
    return () => clearTimeout(t)
  }, [])

  return (
    <div className="space-y-6 animate-fade-in">
      <SectionHeader
        title="Dashboard"
        subtitle="Thống kê thị trường IT"
        action={
          <button
            onClick={() => { setLoading(true); setTimeout(() => setLoading(false), 1000) }}
            className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors"
          >
            <RefreshCw size={13} /> Làm mới
          </button>
        }
      />

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Tổng tin tuyển dụng" value="8,420" sub="↑ 12% so tháng trước" color="text-indigo" />
        <StatCard label="Lương trung bình"     value="$1,560" sub="↑ 5% so Q1"           color="text-violet" />
        <StatCard label="Công ty đang tuyển"   value="1,240"  sub="Mới: 87 tuần này"     color="text-mint-dark" />
        <StatCard label="Skills trending"      value="ReactJS" sub="↑ 15% nhu cầu"       color="text-text-primary" />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Skill bar */}
        <ChartCard
          title="Top 10 Kỹ năng phổ biến"
          loading={loading}
          footer={
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-2xs text-text-muted">
                <span className="w-2 h-2 rounded-full bg-indigo inline-block" />
                Data from VietnamWorks
              </div>
              <UpdateBadge />
            </div>
          }
        >
          <SkillBarChart data={SKILL_DATA} />
        </ChartCard>

        {/* Salary box */}
        <ChartCard
          title="Phân phối mức lương (USD/tháng)"
          subtitle="Junior · Mid · Senior"
          loading={loading}
          footer={
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 text-xs text-text-secondary">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-1 bg-[#7C3AED] inline-block rounded" /> Trung vị
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 border border-[#7C3AED] bg-violet-bg inline-block rounded-sm" /> IQR
                </span>
              </div>
              <UpdateBadge />
            </div>
          }
        >
          <SalaryBoxPlot data={SALARY_BOX_DATA} />
        </ChartCard>
      </div>

      {/* Trend line */}
      <ChartCard
        title="Xu hướng tuyển dụng theo thời gian"
        loading={loading}
        action={
          <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-0.5">
            {['3M', '6M', '12M'].map(r => (
              <button
                key={r}
                onClick={() => setTrendRange(r)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  trendRange === r
                    ? 'bg-white shadow text-indigo'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        }
      >
        <TrendLineChart data={TREND_MAP[trendRange]} />
      </ChartCard>
    </div>
  )
}
