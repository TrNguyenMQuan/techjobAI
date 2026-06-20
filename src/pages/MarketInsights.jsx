import { useState } from 'react'
import { TrendingUp, Info } from 'lucide-react'
import { AIBadge, SectionHeader, Card } from '../components/ui'
import { MarketSalaryChart } from '../components/charts'
import { MARKET_SALARY_DATA, EMERGING_SKILLS } from '../data/mockData'

// ─── Vietnam heatmap (SVG placeholder) ───────────────────────────────────────
function VietnamMap() {
  const cities = [
    { name: 'TP.HCM', x: 195, y: 290, pct: 55, r: 18 },
    { name: 'Hà Nội', x: 185, y: 88,  pct: 35, r: 14 },
    { name: 'Đà Nẵng', x: 195, y: 185, pct: 10, r: 9 },
  ]

  return (
    <div className="relative">
      <svg viewBox="0 0 380 420" className="w-full max-h-64" style={{ filter: 'drop-shadow(0 2px 8px rgba(0,0,0,0.08))' }}>
        {/* Simplified Vietnam outline */}
        <path
          d="M175,20 L210,25 L230,40 L245,60 L240,90 L220,110 L215,130 L210,150
             L215,165 L225,175 L230,190 L220,210 L200,230 L195,250 L200,270
             L215,285 L225,300 L220,320 L205,340 L185,355 L165,360 L150,345
             L145,325 L155,305 L160,285 L150,265 L140,245 L145,225 L155,210
             L160,190 L150,170 L145,150 L155,130 L160,110 L155,90 L160,70
             L170,50 Z"
          fill="#1E1B4B"
          opacity="0.85"
          stroke="#312E81"
          strokeWidth="1.5"
        />

        {/* City hotspots */}
        {cities.map(c => (
          <g key={c.name}>
            <circle cx={c.x} cy={c.y} r={c.r + 4} fill="#10B981" opacity={0.2} />
            <circle cx={c.x} cy={c.y} r={c.r} fill="#10B981" opacity={0.85} />
            <text x={c.x + c.r + 4} y={c.y + 4} fontSize={9} fill="#374151" fontWeight={600}>{c.name}</text>
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div className="absolute top-2 right-2 bg-white rounded-lg shadow-card border border-gray-100 p-3">
        <p className="text-xs font-semibold text-text-primary mb-2">Top Hubs</p>
        {cities.map(c => (
          <div key={c.name} className="flex items-center gap-2 mb-1 text-xs text-text-secondary">
            <span className="w-2 h-2 rounded-full bg-mint shrink-0" />
            {c.name} <span className="ml-auto font-semibold text-text-primary">{c.pct}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Emerging skill row ────────────────────────────────────────────────────────
function EmergingSkillRow({ skill }) {
  return (
    <div className="flex items-center gap-3 py-3 border-b border-gray-100 last:border-0">
      <div
        className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold shrink-0"
        style={{ backgroundColor: skill.color }}
      >
        {skill.label}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-text-primary">{skill.name}</p>
        <p className="text-xs text-text-secondary">{skill.desc}</p>
      </div>
      <div className="flex items-center gap-1 text-mint font-bold text-sm shrink-0">
        <TrendingUp size={13} />
        {skill.growth}
      </div>
    </div>
  )
}

// ─── Filter tabs ──────────────────────────────────────────────────────────────
const HEATMAP_TABS = ['All Roles', 'AI/Data', 'Engineering']

export default function MarketInsights() {
  const [activeTab, setActiveTab] = useState('All Roles')

  return (
    <div className="animate-fade-in space-y-5">
      <SectionHeader
        title="Market Insights"
        subtitle="Phân tích chuyên sâu thị trường IT Việt Nam"
      />

      {/* AI State of the Market banner */}
      <Card className="p-5">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-violet/10 flex items-center justify-center shrink-0">
            <TrendingUp size={18} className="text-violet" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-base font-bold text-text-primary">State of the Market: Q3 Analysis</h3>
              <AIBadge variant="violet">✨ AI INSIGHTS</AIBadge>
            </div>
            <p className="text-sm text-text-secondary leading-relaxed">
              Nhu cầu tuyển dụng kỹ sư Mid-to-Senior tại Việt Nam đã ổn định, với mức tăng đáng kể <strong>+15%</strong> các vị trí yêu cầu AI/ML. Hệ sinh thái JavaScript truyền thống (React/Node) vẫn là driver lớn nhất về volume, nhưng các vai trò backend chuyên sâu (Go, Python) có premium lương trung bình <strong>+12%</strong>. Remote work flexibility tiếp tục là điểm thương lượng chính với top talent.
            </p>
          </div>
        </div>
      </Card>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Salary comparison */}
        <Card className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-text-primary">Salary Comparison by Tech Stack</h3>
            <div className="flex items-center gap-1 text-xs text-text-muted">
              <Info size={12} />
              Median USD/Month
            </div>
          </div>
          <MarketSalaryChart data={MARKET_SALARY_DATA} />
        </Card>

        {/* Emerging skills */}
        <Card className="p-5">
          <h3 className="text-base font-semibold text-text-primary mb-4">Emerging Skills Growth</h3>
          <div>
            {EMERGING_SKILLS.map(s => <EmergingSkillRow key={s.id} skill={s} />)}
          </div>
          <div className="mt-3 pt-3 border-t border-gray-100">
            <AIBadge variant="mint">📊 Generated from live data</AIBadge>
            <p className="text-2xs text-text-muted mt-1">Dựa trên 8,420 tin tuyển dụng · Cập nhật hàng ngày</p>
          </div>
        </Card>
      </div>

      {/* Vietnam heatmap */}
      <Card className="p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-text-primary">Tech Talent Demand Heatmap</h3>
          <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-0.5">
            {HEATMAP_TABS.map(t => (
              <button
                key={t}
                onClick={() => setActiveTab(t)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                  activeTab === t
                    ? 'bg-white shadow text-indigo'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
        <div className="max-w-sm mx-auto">
          <VietnamMap />
        </div>
      </Card>

      {/* Quick stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'ReactJS jobs', value: '1,245', sub: '+15% this month', color: 'text-indigo' },
          { label: 'Avg. React salary', value: '$1,680', sub: 'Mid-level TP.HCM', color: 'text-violet' },
          { label: 'Remote jobs', value: '38%', sub: 'của tổng tin đăng', color: 'text-mint-dark' },
          { label: 'AI/ML openings', value: '+312%', sub: 'YoY growth', color: 'text-amber-600' },
        ].map(s => (
          <Card key={s.label} className="p-4">
            <p className="text-xs text-text-secondary mb-1">{s.label}</p>
            <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-mint mt-1">{s.sub}</p>
          </Card>
        ))}
      </div>
    </div>
  )
}
