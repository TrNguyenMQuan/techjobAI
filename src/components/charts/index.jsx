import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line, Legend, Cell,
} from 'recharts'

// ─── Shared custom tooltip ────────────────────────────────────────────────────
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white rounded-lg shadow-modal border border-gray-100 px-3 py-2 text-xs">
      {label && <p className="font-semibold text-text-primary mb-1">{label}</p>}
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color || p.fill }} />
          <span className="text-text-secondary">{p.name}:</span>
          <span className="font-semibold text-text-primary">
            {typeof p.value === 'number' && p.name?.toLowerCase().includes('lương')
              ? `$${p.value.toLocaleString()}`
              : p.value}
          </span>
        </div>
      ))}
    </div>
  )
}

// ─── Chart 1: Top 10 skills horizontal bar ───────────────────────────────────
export function SkillBarChart({ data }) {
  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const d = payload[0].payload
    return (
      <div className="bg-white rounded-lg shadow-modal border border-gray-100 px-3 py-2 text-xs">
        <p className="font-semibold text-text-primary mb-1">{d.skill}</p>
        <p className="text-text-secondary">{d.jobs.toLocaleString()} tin tuyển dụng</p>
        <p className="text-violet font-medium">{d.pct}% tổng số tin</p>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 0, right: 60, left: 0, bottom: 0 }}
        barCategoryGap="25%"
      >
        <CartesianGrid horizontal={false} stroke="#F3F4F6" />
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="skill"
          tick={{ fontSize: 12, fill: '#6B7280' }}
          tickLine={false}
          axisLine={false}
          width={80}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: '#F8F7FF' }} />
        <Bar dataKey="jobs" radius={[0, 4, 4, 0]} maxBarSize={14}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ─── Chart 2: Salary box plot (rendered manually) ────────────────────────────
function BoxPlotBar({ entry, xOffset, barWidth, scaleY, chartHeight, padding }) {
  const y    = v => chartHeight - padding - scaleY(v)
  const cx   = xOffset + barWidth / 2

  return (
    <g>
      {/* Whisker line (min-max) */}
      <line x1={cx} y1={y(entry.min)} x2={cx} y2={y(entry.max)}
        stroke="#CBD5E1" strokeWidth={1.5} />
      {/* Min cap */}
      <line x1={cx - 6} y1={y(entry.min)} x2={cx + 6} y2={y(entry.min)}
        stroke="#CBD5E1" strokeWidth={1.5} />
      {/* Max cap */}
      <line x1={cx - 6} y1={y(entry.max)} x2={cx + 6} y2={y(entry.max)}
        stroke="#CBD5E1" strokeWidth={1.5} />
      {/* IQR box */}
      <rect
        x={xOffset + 8}
        y={y(entry.q3)}
        width={barWidth - 16}
        height={y(entry.q1) - y(entry.q3)}
        fill="#EDE9FE"
        stroke="#7C3AED"
        strokeWidth={1.5}
        rx={3}
      />
      {/* Median line */}
      <line
        x1={xOffset + 8} y1={y(entry.median)}
        x2={xOffset + barWidth - 8} y2={y(entry.median)}
        stroke="#7C3AED" strokeWidth={2.5}
      />
      {/* Level label */}
      <text x={cx} y={chartHeight - 4} textAnchor="middle"
        fontSize={11} fill="#6B7280" fontWeight={600}>
        {entry.level}
      </text>
    </g>
  )
}

export function SalaryBoxPlot({ data }) {
  const [hovered, setHovered] = useState(null)
  const chartHeight = 220
  const chartWidth  = 460
  const padding     = 24
  const barWidth    = (chartWidth - padding * 2) / data.length

  const allVals = data.flatMap(d => [d.min, d.max])
  const domainMin = Math.min(...allVals) - 100
  const domainMax = Math.max(...allVals) + 100
  const range     = domainMax - domainMin
  const scaleY    = v => ((v - domainMin) / range) * (chartHeight - padding * 2)

  // Y-axis ticks
  const yTicks = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000].filter(
    t => t >= domainMin && t <= domainMax
  )

  return (
    <div className="relative">
      <svg width="100%" viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="overflow-visible">
        {/* Y-axis grid + labels */}
        {yTicks.map(t => {
          const y = chartHeight - padding - scaleY(t)
          return (
            <g key={t}>
              <line x1={padding} y1={y} x2={chartWidth - 10} y2={y}
                stroke="#F3F4F6" strokeWidth={1} />
              <text x={padding - 4} y={y + 4} textAnchor="end"
                fontSize={10} fill="#9CA3AF">
                ${t >= 1000 ? `${t/1000}k` : t}
              </text>
            </g>
          )
        })}

        {/* Boxes */}
        {data.map((entry, i) => (
          <g key={entry.level} onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)}>
            <BoxPlotBar
              entry={entry}
              xOffset={padding + i * barWidth}
              barWidth={barWidth}
              scaleY={scaleY}
              chartHeight={chartHeight}
              padding={padding}
            />
          </g>
        ))}

        {/* Hover tooltip */}
        {hovered !== null && (() => {
          const d = data[hovered]
          const cx = padding + hovered * barWidth + barWidth / 2
          return (
            <g transform={`translate(${cx + 10}, ${chartHeight * 0.2})`}>
              <rect x={0} y={0} width={130} height={90} rx={6}
                fill="white" stroke="#E5E7EB" strokeWidth={1}
                filter="drop-shadow(0 2px 8px rgba(0,0,0,0.08))" />
              <text x={8} y={18} fontSize={11} fontWeight={700} fill="#1E1B4B">{d.level}</text>
              {[
                ['Max',    d.max],
                ['Q3',     d.q3],
                ['Median', d.median],
                ['Q1',     d.q1],
                ['Min',    d.min],
              ].map(([k, v], j) => (
                <g key={k}>
                  <text x={8}   y={32 + j * 13} fontSize={10} fill="#6B7280">{k}</text>
                  <text x={90}  y={32 + j * 13} fontSize={10} fill="#4338CA" fontWeight={600}>
                    ${v.toLocaleString()}
                  </text>
                </g>
              ))}
            </g>
          )
        })()}
      </svg>
    </div>
  )
}

// ─── Chart 3: Trend multi-line chart ────────────────────────────────────────
export function TrendLineChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ top: 4, right: 16, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
        <XAxis
          dataKey="month"
          tick={{ fontSize: 11, fill: '#9CA3AF' }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} tickLine={false} axisLine={false} />
        <Tooltip content={<ChartTooltip />} />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
        />
        <Line
          type="monotone"
          dataKey="jobs"
          name="Số tin tuyển dụng"
          stroke="#4338CA"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, strokeWidth: 0 }}
        />
        <Line
          type="monotone"
          dataKey="salary"
          name="Lương trung bình"
          stroke="#7C3AED"
          strokeWidth={2}
          dot={false}
          strokeDasharray="4 2"
          activeDot={{ r: 4, strokeWidth: 0 }}
        />
        <Line
          type="monotone"
          dataKey="demand"
          name="Top Skill Demand"
          stroke="#10B981"
          strokeWidth={2.5}
          dot={false}
          activeDot={{ r: 4, strokeWidth: 0 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

// ─── Market Insights: Salary Comparison stacked bar ─────────────────────────
export function MarketSalaryChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }} barGap={2}>
        <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
        <XAxis dataKey="stack" tick={{ fontSize: 10, fill: '#9CA3AF' }} tickLine={false} axisLine={false} />
        <YAxis tick={{ fontSize: 10, fill: '#9CA3AF' }} tickLine={false} axisLine={false}
          tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: '#F8F7FF' }} />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, paddingTop: 6 }} />
        <Bar dataKey="junior" name="Junior" stackId="a" fill="#C4B5FD" radius={[0,0,0,0]} maxBarSize={24} />
        <Bar dataKey="mid"    name="Mid"    stackId="a" fill="#7C3AED" maxBarSize={24} />
        <Bar dataKey="senior" name="Senior" stackId="a" fill="#10B981" radius={[4,4,0,0]} maxBarSize={24} />
      </BarChart>
    </ResponsiveContainer>
  )
}
