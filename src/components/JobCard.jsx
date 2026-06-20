import { useNavigate } from 'react-router-dom'
import clsx from 'clsx'
import { MapPin, Clock, Bookmark, ArrowRight } from 'lucide-react'
import { useApp } from '../context/AppContext'
import { Skeleton, AIBadge, SkillTag, LevelBadge } from './ui'

// ─── Skeleton loader ──────────────────────────────────────────────────────────
export function JobCardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-card border border-gray-100 p-5 space-y-3">
      <div className="flex items-start gap-3">
        <Skeleton className="w-10 h-10 rounded-lg shrink-0" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      <Skeleton className="h-3 w-1/3" />
      <div className="flex gap-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
        <Skeleton className="h-6 w-14 rounded-full" />
      </div>
    </div>
  )
}

// ─── Company logo / initial ──────────────────────────────────────────────────
function CompanyLogo({ job }) {
  if (job.companyLogo) {
    return <img src={job.companyLogo} alt={job.company} className="w-10 h-10 rounded-lg object-contain border border-gray-100" />
  }
  return (
    <div
      className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-base shrink-0"
      style={{ backgroundColor: job.companyColor || '#4338CA' }}
    >
      {job.companyInitial || job.company?.[0]?.toUpperCase() || '?'}
    </div>
  )
}

// ─── Main JobCard ─────────────────────────────────────────────────────────────
export default function JobCard({ job, compact = false }) {
  const navigate      = useNavigate()
  const { toggleSaved } = useApp()

  // Show at most 4 skills, rest collapsed to "+N"
  const MAX_TAGS = 4
  const visibleSkills = job.skills?.slice(0, MAX_TAGS) || []
  const extraCount    = (job.skills?.length || 0) - MAX_TAGS

  const showAIEstimate = job.salaryRaw === 'Thỏa thuận' || job.salaryRaw === null && !job.salaryMin

  return (
    <div
      className={clsx(
        'job-card bg-white rounded-lg shadow-card border border-gray-100 cursor-pointer select-none',
        compact ? 'p-3.5' : 'p-5'
      )}
      onClick={() => navigate(`/jobs/${job.id}`)}
    >
      {/* Header row */}
      <div className="flex items-start gap-3 mb-3">
        <CompanyLogo job={job} />

        <div className="flex-1 min-w-0">
          <h3 className={clsx(
            'font-semibold text-text-primary leading-snug truncate',
            compact ? 'text-sm' : 'text-base'
          )}>
            {job.title}
          </h3>
          <p className="text-xs text-text-secondary mt-0.5 truncate">
            {job.company}
            {job.location && <span className="text-text-muted"> · {job.location}</span>}
          </p>
        </div>

        {/* Bookmark */}
        <button
          onClick={e => { e.stopPropagation(); toggleSaved(job.id) }}
          className={clsx(
            'p-1.5 rounded-lg transition-colors shrink-0',
            job.saved
              ? 'text-violet bg-violet-bg'
              : 'text-text-muted hover:text-violet hover:bg-violet-bg'
          )}
          title={job.saved ? 'Bỏ lưu' : 'Lưu tin'}
        >
          <Bookmark size={15} fill={job.saved ? 'currentColor' : 'none'} />
        </button>
      </div>

      {/* Salary + type row */}
      <div className="flex items-center flex-wrap gap-x-4 gap-y-1 mb-3">
        <div className="flex items-center gap-1.5 text-sm font-semibold text-text-primary">
          <span>💰</span>
          {job.salaryRaw === 'Thỏa thuận' ? (
            <span className="text-text-secondary font-medium">Thỏa thuận</span>
          ) : (
            <span>{job.salaryDisplay}</span>
          )}
        </div>

        {job.type && (
          <div className="flex items-center gap-1 text-xs text-text-secondary">
            <Clock size={11} />
            <span>{job.type}</span>
          </div>
        )}

        {job.location && (
          <div className="flex items-center gap-1 text-xs text-text-secondary">
            <MapPin size={11} />
            <span>{job.location}</span>
          </div>
        )}
      </div>

      {/* AI estimated salary */}
      {job.aiEstimatedSalary && (showAIEstimate || !compact) && (
        <div className="mb-3">
          <AIBadge variant="mint">
            🤖 AI Estimated: ~${job.aiEstimatedSalary.toLocaleString()}
          </AIBadge>
        </div>
      )}

      {/* Skills */}
      {!compact && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {visibleSkills.map(s => (
            <SkillTag key={s} variant="plain">{s}</SkillTag>
          ))}
          {extraCount > 0 && (
            <SkillTag variant="preferred">+{extraCount} more</SkillTag>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-gray-50">
        <div className="flex items-center gap-2">
          {job.level && <LevelBadge level={job.level} />}
          {job.postedDate && (
            <span className="text-2xs text-text-muted">{job.postedDate}</span>
          )}
        </div>
        <div className="flex items-center gap-1 text-xs text-violet font-medium">
          Xem chi tiết <ArrowRight size={12} />
        </div>
      </div>
    </div>
  )
}

// ─── Mini job card (for chat bubbles) ─────────────────────────────────────────
export function MiniJobCard({ job }) {
  const navigate = useNavigate()
  if (!job) return null
  return (
    <div
      className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200 cursor-pointer hover:border-violet/40 hover:bg-violet-bg/30 transition-all"
      onClick={() => navigate(`/jobs/${job.id}`)}
    >
      <div
        className="w-8 h-8 rounded-md flex items-center justify-center text-white text-xs font-bold shrink-0"
        style={{ backgroundColor: job.companyColor || '#4338CA' }}
      >
        {job.companyInitial || job.company?.[0]}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-text-primary truncate">{job.title}</p>
        <p className="text-2xs text-text-secondary truncate">
          {job.company} · {job.location}
        </p>
      </div>
      {job.salaryDisplay && (
        <span className="text-xs font-semibold text-mint shrink-0">{job.salaryDisplay}</span>
      )}
    </div>
  )
}
