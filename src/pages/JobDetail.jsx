import { useParams, useNavigate, Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import {
  MapPin, Clock, Bookmark, Share2, ExternalLink,
  ChevronRight, Bot, Calendar, Briefcase,
} from 'lucide-react'
import { useApp } from '../context/AppContext'
import { getJobById, getRelatedJobs } from '../services/jobService'
import { normalizeJob } from '../services/jobService'
import {
  Button, AIBadge, SkillTag, Card, Skeleton,
} from '../components/ui'
import clsx from 'clsx'

function DetailSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-7 w-2/3" />
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-32 w-full" />
    </div>
  )
}

export default function JobDetail() {
  const { id }              = useParams()
  const navigate            = useNavigate()
  const { jobs, toggleSaved, settings, isJobSaved } = useApp()

  const [loading, setLoading] = useState(true)
  const [job, setJob] = useState(null)
  const [related, setRelated] = useState([])
  const [salaryPrediction, setSalaryPrediction] = useState(null)

  useEffect(() => {
    setLoading(true)
    setJob(null)
    setRelated([])
    setSalaryPrediction(null)

    // Try to find the job in the in-memory store first (instant)
    const cached = jobs.find(j => j.id === id)
    
    // Always fetch from API for full details
    getJobById(id)
      .then(data => {
        const normalized = normalizeJob(data)
        setJob(normalized)
        
        // Fetch salary prediction if salary is negotiable
        if (normalized.salaryRaw === 'Thỏa thuận') {
          import('../services/api').then(({ api }) => {
            const skills = Array.isArray(normalized.skills) ? normalized.skills.join(',') : ''
            api.post('/predict-salary', null, {
              params: {
                title: normalized.title,
                city: normalized.location || 'unknown',
                level: normalized.level || 'unknown',
                work_mode: normalized.type || 'unknown',
                skills,
              }
            }).then(res => {
              if (res.data && !res.data.error) {
                setSalaryPrediction(res.data)
              }
            }).catch(() => {})
          })
        }
      })
      .catch(() => {
        // Fallback to cached data if API fails
        if (cached) setJob(cached)
      })
      .finally(() => setLoading(false))

    // Fetch related jobs from API
    getRelatedJobs(id)
      .then(data => {
        const items = data?.data || data || []
        setRelated(Array.isArray(items) ? items.map(normalizeJob) : [])
      })
      .catch(() => setRelated([]))
  }, [id, jobs])

  if (!loading && !job) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="text-5xl mb-4">🔍</div>
        <h2 className="text-xl font-bold text-text-primary mb-2">Không tìm thấy tin tuyển dụng</h2>
        <p className="text-text-secondary mb-5">Tin này có thể đã bị xoá hoặc không tồn tại.</p>
        <Button onClick={() => navigate('/jobs')}>← Quay lại danh sách</Button>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-xs text-text-muted mb-5">
        <Link to="/jobs" className="hover:text-violet transition-colors">Job Search</Link>
        <ChevronRight size={12} />
        {job?.skills?.[0] && <><span className="hover:text-violet cursor-pointer">{job.skills[0]}</span><ChevronRight size={12} /></>}
        <span className="text-text-primary font-medium">{job?.title || '…'}</span>
      </nav>

      <div className="flex gap-6 items-start">
        {/* ── Left column (65%) ── */}
        <div className="flex-1 min-w-0">
          {loading ? <DetailSkeleton /> : (
            <>
              {/* Header */}
              <Card className="p-6 mb-5">
                <div className="flex items-start gap-4 mb-4">
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-lg shrink-0"
                    style={{ backgroundColor: job.companyColor }}
                  >
                    {job.companyInitial}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h1 className="text-xl font-bold text-text-primary">{job.title}</h1>
                    <p className="text-sm text-violet font-medium mt-0.5">{job.company}</p>
                    <div className="flex flex-wrap gap-3 mt-2">
                      <span className="flex items-center gap-1 text-xs text-text-secondary"><MapPin size={12} />{job.location}</span>
                      {job.type && <span className="flex items-center gap-1 text-xs text-text-secondary"><Briefcase size={12} />{job.type}</span>}
                      <span className="flex items-center gap-1 text-xs text-text-secondary"><Clock size={12} />Đăng {job.postedDate}</span>
                    </div>
                  </div>
                </div>

                {/* Salary */}
                <div className="flex items-center flex-wrap gap-3">
                  <div className="text-lg font-bold text-text-primary">
                    {job.salaryRaw === 'Thỏa thuận' ? 'Thỏa thuận' : job.salaryDisplay}
                    <span className="text-xs font-normal text-text-muted ml-1">/month</span>
                  </div>
                  {settings.salaryEstimate && salaryPrediction && (
                    <AIBadge variant="mint">
                      <Bot size={11} />
                      ~{Number(salaryPrediction.predicted_min_vnd || 0).toLocaleString('vi-VN')} – {Number(salaryPrediction.predicted_max_vnd || 0).toLocaleString('vi-VN')} VND (AI)
                    </AIBadge>
                  )}
                  {settings.salaryEstimate && job.aiEstimatedSalary && !salaryPrediction && (
                    <AIBadge variant="mint">
                      <Bot size={11} />
                      ~ {job.aiEstimatedSalary.toLocaleString('vi-VN')} VND (AI)
                    </AIBadge>
                  )}
                  <span className="text-xs text-text-muted">Posted {job.postedDate}</span>
                </div>
              </Card>

              {/* About the role */}
              <Card className="p-6 mb-5">
                <h2 className="text-base font-semibold text-text-primary mb-3">About the Role</h2>
                <div className="text-sm text-text-secondary leading-relaxed whitespace-pre-line"
                  dangerouslySetInnerHTML={{ __html: job.description || job.job_description || 'Chưa có mô tả chi tiết.' }}
                />

                {/* Job Requirements */}
                {(job.job_requirement || job.responsibilities?.length > 0) && (
                  <>
                    <h3 className="text-sm font-semibold text-text-primary mt-5 mb-2">Requirements</h3>
                    {job.responsibilities?.length > 0 ? (
                      <ul className="space-y-2">
                        {job.responsibilities.map((r, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                            <span className="w-1.5 h-1.5 rounded-full bg-violet mt-1.5 shrink-0" />
                            {r}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-sm text-text-secondary leading-relaxed whitespace-pre-line"
                        dangerouslySetInnerHTML={{ __html: job.job_requirement || '' }}
                      />
                    )}
                  </>
                )}
              </Card>

              {/* Skills */}
              <Card className="p-6 mb-5">
                <h2 className="text-base font-semibold text-text-primary mb-4">Skills & Requirements</h2>
                <div className="mb-4">
                  <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">Required Skills</p>
                  <div className="flex flex-wrap gap-2">
                    {(job.requiredSkills || job.skills || []).map(s => <SkillTag key={s} variant="required">{s}</SkillTag>)}
                  </div>
                </div>
                {job.preferredSkills?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">Preferred Skills</p>
                    <div className="flex flex-wrap gap-2">
                      {job.preferredSkills.map(s => <SkillTag key={s} variant="preferred">{s}</SkillTag>)}
                    </div>
                  </div>
                )}
              </Card>

              {/* Benefits */}
              {job.benefits && (typeof job.benefits === 'string' ? job.benefits.length > 0 : job.benefits?.length > 0) && (
                <Card className="p-6 mb-5">
                  <h2 className="text-base font-semibold text-text-primary mb-3">Benefits</h2>
                  {typeof job.benefits === 'string' ? (
                    <div className="text-sm text-text-secondary leading-relaxed whitespace-pre-line"
                      dangerouslySetInnerHTML={{ __html: job.benefits }}
                    />
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {job.benefits.map(b => (
                        <span key={b} className="text-xs px-3 py-1.5 bg-mint-bg text-mint-dark rounded-full font-medium">✓ {b}</span>
                      ))}
                    </div>
                  )}
                </Card>
              )}

              {/* Meta */}
              <Card className="p-5 mb-5">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-2xs text-text-muted uppercase tracking-wider mb-1">Ngày đăng</p>
                    <p className="text-sm font-medium text-text-primary flex items-center gap-1"><Calendar size={12} />{job.postedDate || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-2xs text-text-muted uppercase tracking-wider mb-1">Nguồn</p>
                    <p className="text-sm font-medium text-text-primary">VietnamWorks</p>
                  </div>
                </div>
              </Card>
            </>
          )}
        </div>

        {/* ── Right sticky panel (35%) ── */}
        <div className="hidden lg:block w-72 shrink-0">
          {loading ? (
            <Card className="p-5 space-y-3">
              <Skeleton className="h-10 w-full rounded-lg" />
              <Skeleton className="h-10 w-full rounded-lg" />
              <Skeleton className="h-20 w-full rounded-lg" />
            </Card>
          ) : (
            <div className="sticky top-20 space-y-4">
              <Card className="p-5">
                <Button
                  variant="primary"
                  className="w-full mb-2"
                  onClick={() => window.open(job.sourceUrl, '_blank')}
                >
                  Apply at Source <ExternalLink size={13} />
                </Button>
                <Button
                  variant="outline"
                  className="w-full mb-3"
                  onClick={() => navigate(`/cover-letter?jobId=${job.id}`)}
                >
                  ✍️ Write Cover Letter
                </Button>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="flex-1"
                    onClick={() => toggleSaved(job.id, job)}
                  >
                    <Bookmark size={13} fill={isJobSaved(job.id) ? 'currentColor' : 'none'} className={clsx(isJobSaved(job.id) && 'text-violet')} />
                    {isJobSaved(job.id) ? 'Saved' : 'Save Job'}
                  </Button>
                  <Button variant="ghost" size="sm" className="flex-1">
                    <Share2 size={13} /> Share
                  </Button>
                </div>
              </Card>

              {/* Company info */}
              <Card className="p-5">
                <h3 className="text-sm font-semibold text-text-primary mb-3">About {job.company}</h3>
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold shrink-0"
                    style={{ backgroundColor: job.companyColor }}
                  >
                    {job.companyInitial}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-text-primary">{job.company}</p>
                    <p className="text-xs text-text-secondary">VietnamWorks Employer</p>
                  </div>
                </div>
                <p className="text-xs text-text-secondary leading-relaxed mb-3">
                  {job.company} là công ty công nghệ hàng đầu, chuyên phát triển các sản phẩm AI-driven phục vụ doanh nghiệp.
                </p>
              </Card>

              {/* AI Salary Prediction */}
              {settings.salaryEstimate && salaryPrediction && (
                <Card className="p-5 border-mint/30 bg-mint-bg/30">
                  <h3 className="text-sm font-semibold text-text-primary mb-2 flex items-center gap-1.5">
                    <Bot size={14} className="text-mint" /> AI Salary Prediction
                  </h3>
                  <p className="text-lg font-bold text-mint mb-1">
                    {Number(salaryPrediction.predicted_min_vnd || 0).toLocaleString('vi-VN')} – {Number(salaryPrediction.predicted_max_vnd || 0).toLocaleString('vi-VN')} VND
                  </p>
                  <p className="text-2xs text-text-muted">Dự đoán bởi mô hình AI dựa trên dữ liệu thị trường</p>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Mobile actions bar */}
      {!loading && job && (
        <>
          {/* Spacer so the fixed bar below never overlaps page content */}
          <div className="lg:hidden h-20" />
          <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-3 flex gap-2 z-30">
            <Button variant="primary" className="flex-1" onClick={() => window.open(job.sourceUrl, '_blank')}>
              Apply at Source <ExternalLink size={13} />
            </Button>
            <Button variant="outline" size="md" onClick={() => toggleSaved(job.id, job)}>
              <Bookmark size={15} fill={isJobSaved(job.id) ? 'currentColor' : 'none'} />
            </Button>
          </div>
        </>
      )}

      {/* Related jobs */}
      {!loading && related.length > 0 && (
        <div className="mt-8">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-sm font-semibold text-text-primary">🔗 Similar Roles</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {related.map(j => (
              <div key={j.id} className="bg-white rounded-lg border border-gray-100 p-4 cursor-pointer hover:border-violet/40 hover:shadow-hover transition-all" onClick={() => navigate(`/jobs/${j.id}`)}>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-6 h-6 rounded text-white text-xs font-bold flex items-center justify-center shrink-0" style={{ backgroundColor: j.companyColor }}>{j.companyInitial}</div>
                  <p className="text-xs font-semibold text-text-primary truncate">{j.title}</p>
                </div>
                <p className="text-2xs text-text-secondary mb-2">{j.company} · {j.location}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-mint">{j.salaryDisplay}</span>
                  <span className="text-2xs text-text-muted">{j.postedDate}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
