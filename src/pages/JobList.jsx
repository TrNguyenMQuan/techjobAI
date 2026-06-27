import { useState, useEffect, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Filter, Sparkles, ChevronDown } from 'lucide-react'
import { useApp } from '../context/AppContext'
import JobCard, { JobCardSkeleton } from '../components/JobCard'
import { SectionHeader, AIBadge, Button, EmptyState } from '../components/ui'
import { LOCATIONS, JOB_LEVELS, WORK_TYPES, SALARY_RANGES } from '../data/mockData'
import { searchJobsSemantic, getJobs } from '../services/jobService'
import clsx from 'clsx'

// ─── AI Recommended banner ────────────────────────────────────────────────────
function AIRecommendBanner() {
  return (
    <div className="bg-white rounded-lg border border-violet/30 p-4 mb-4 flex items-start gap-3">
      <div className="w-8 h-8 rounded-lg bg-violet/10 flex items-center justify-center shrink-0 mt-0.5">
        <Sparkles size={15} className="text-violet" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-semibold text-text-primary">AI Recommended Filters</span>
          <AIBadge variant="violet">✨ AI INSIGHTS</AIBadge>
        </div>
        <p className="text-xs text-text-secondary mb-2">
          Based on your &ldquo;ReactJS&rdquo; profile, we suggest focusing on Mid-to-Senior level roles in TP.HCM or Remote to maximize your expected salary.
        </p>
        <div className="flex gap-2 flex-wrap">
          {['+ React Ecosystem', '+ Fintech Sector'].map(t => (
            <button key={t} className="text-xs px-2.5 py-1 rounded-full border border-violet/40 text-violet hover:bg-violet-bg transition-colors">{t}</button>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Filter sidebar ───────────────────────────────────────────────────────────
function FilterPanel({ filters, onChange, onClear }) {
  const toggle = (key, val) => {
    const cur = filters[key] || []
    onChange(key, cur.includes(val) ? cur.filter(v => v !== val) : [...cur, val])
  }

  return (
    <div className="bg-white rounded-lg shadow-card border border-gray-100 p-5 space-y-5 sticky top-20">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary flex items-center gap-1.5">
          <Filter size={14} /> Filters
        </h3>
        <button onClick={onClear} className="text-xs text-text-muted hover:text-red-500 transition-colors">Clear all</button>
      </div>

      {/* Location */}
      <div>
        <p className="text-2xs font-semibold text-text-muted uppercase tracking-wider mb-2">Location</p>
        <div className="space-y-1.5">
          {LOCATIONS.map(loc => (
            <label key={loc} className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                checked={(filters.locations || []).includes(loc)}
                onChange={() => toggle('locations', loc)}
                className="w-4 h-4 rounded border-gray-300 text-indigo focus:ring-violet/30 cursor-pointer"
              />
              <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">{loc}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Salary range */}
      <div>
        <p className="text-2xs font-semibold text-text-muted uppercase tracking-wider mb-2">Salary range (monthly)</p>
        <select
          value={filters.salaryKey || ''}
          onChange={e => onChange('salaryKey', e.target.value)}
          className="w-full text-sm px-2.5 py-1.5 border border-gray-200 rounded focus:outline-none focus:border-violet"
        >
          {SALARY_RANGES.map(r => (
            <option key={r.label} value={r.label}>{r.label}</option>
          ))}
        </select>
      </div>

      {/* Job level */}
      <div>
        <p className="text-2xs font-semibold text-text-muted uppercase tracking-wider mb-2">Job level</p>
        <div className="flex flex-wrap gap-2">
          {JOB_LEVELS.map(l => (
            <button
              key={l}
              onClick={() => toggle('levels', l)}
              className={clsx(
                'px-2.5 py-1 rounded-full text-xs font-medium border transition-all',
                (filters.levels || []).includes(l)
                  ? 'bg-indigo text-white border-indigo'
                  : 'border-gray-200 text-text-secondary hover:border-violet hover:text-violet'
              )}
            >
              {l}
            </button>
          ))}
        </div>
      </div>

      {/* Work type */}
      <div>
        <p className="text-2xs font-semibold text-text-muted uppercase tracking-wider mb-2">Work type</p>
        <div className="flex flex-wrap gap-2">
          {WORK_TYPES.map(t => (
            <button
              key={t}
              onClick={() => toggle('types', t)}
              className={clsx(
                'px-2.5 py-1 rounded-full text-xs font-medium border transition-all',
                (filters.types || []).includes(t)
                  ? 'bg-mint text-white border-mint'
                  : 'border-gray-200 text-text-secondary hover:border-mint hover:text-mint'
              )}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Main Job List page ───────────────────────────────────────────────────────
export default function JobList() {
  const { jobs, setJobs } = useApp()
  const [searchParams] = useSearchParams()
  const queryParam = searchParams.get('q') || ''

  const [loading, setLoading]   = useState(() => {
    const savedResults = sessionStorage.getItem('jobSearchResults')
    const savedQuery = sessionStorage.getItem('jobSearchQuery')
    if (savedResults && savedQuery === queryParam) return false
    return true
  })
  const [searchResults, setSearchResults] = useState(() => {
    const savedResults = sessionStorage.getItem('jobSearchResults')
    const savedQuery = sessionStorage.getItem('jobSearchQuery')
    if (savedResults && savedQuery === queryParam) return JSON.parse(savedResults)
    return null
  })
  const [searchError, setSearchError] = useState('')
  const [filters, setFilters]   = useState({ locations: [], levels: [], types: [], salaryKey: 'Tất cả' })
  const [showFilter, setShowFilter] = useState(false)
  const [page, setPage]         = useState(1)
  const [searchMode, setSearchMode] = useState('exact')
  const PAGE_SIZE = 10

  useEffect(() => {
    // Check cache first to avoid refetching on tab switch
    const savedQuery = sessionStorage.getItem('jobSearchQuery')
    const savedMode = sessionStorage.getItem('jobSearchMode')
    if (searchResults && savedQuery === queryParam && savedMode === searchMode) {
      setLoading(false)
      return
    }

    setLoading(true)
    setSearchError('')
    let cancelled = false

    if (!queryParam.trim() || searchMode === 'exact') {
      getJobs({ keyword: queryParam.trim(), size: 1000, ai_estimate: false })
        .then(result => {
          if (!cancelled) {
            const data = result.data || []
            setSearchResults(data)
            sessionStorage.setItem('jobSearchResults', JSON.stringify(data))
            sessionStorage.setItem('jobSearchQuery', queryParam)
            sessionStorage.setItem('jobSearchMode', searchMode)
          }
        })
        .catch(error => {
          console.error('Failed to fetch jobs:', error)
          if (!cancelled) setSearchError('Không thể tải danh sách việc làm.')
        })
        .finally(() => {
          if (!cancelled) setLoading(false)
        })
      return () => { cancelled = true }
    }

    // Threshold: Only fetch top 50 most relevant jobs to avoid showing irrelevant results
    searchJobsSemantic(queryParam.trim(), 50, false)
      .then(result => {
        if (!cancelled) {
          const results = result.data || []
          setSearchResults(results)
          sessionStorage.setItem('jobSearchResults', JSON.stringify(results))
          sessionStorage.setItem('jobSearchQuery', queryParam)
          sessionStorage.setItem('jobSearchMode', searchMode)
          // Keep fetched jobs available to Job Detail and Cover Letter after
          // the user clicks a semantic-search result.
          setJobs(current => {
            const merged = new Map(current.map(job => [job.id, job]))
            results.forEach(job => merged.set(job.id, { ...merged.get(job.id), ...job }))
            return [...merged.values()]
          })
        }
      })
      .catch(error => {
        console.error('Semantic job search failed:', error)
        if (!cancelled) {
          setSearchResults([])
          setSearchError('Không thể kết nối dịch vụ tìm kiếm AI. Vui lòng thử lại.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [queryParam, searchMode, setJobs])

  const salaryRange = SALARY_RANGES.find(r => r.label === filters.salaryKey) || SALARY_RANGES[0]

  const filtered = useMemo(() => {
    const sourceJobs = searchResults ?? jobs
    return sourceJobs.filter(job => {
      // Semantic results are already ranked by the backend. Only apply exact
      // keyword matching when using the local fallback list.
      if (queryParam && searchResults === null) {
        const q = queryParam.toLowerCase()
        if (!job.title.toLowerCase().includes(q) &&
            !job.company.toLowerCase().includes(q) &&
            !(job.skills || []).some(s => s.toLowerCase().includes(q))) return false
      }
      if (filters.locations?.length && !filters.locations.includes(job.location)) return false
      if (filters.levels?.length && !filters.levels.includes(job.level)) return false
      if (filters.types?.length && !filters.types.includes(job.type)) return false
      const jobMax = job.salaryMax || job.aiEstimatedSalary || 0
      if (salaryRange.max < 99999 && jobMax < salaryRange.min) return false
      return true
    })
  }, [jobs, searchResults, queryParam, filters, salaryRange])

  const paginated = filtered.slice(0, page * PAGE_SIZE)
  const hasMore   = paginated.length < filtered.length

  const setFilter = (key, val) => { setFilters(f => ({ ...f, [key]: val })); setPage(1) }
  const clearFilters = () => { setFilters({ locations: [], levels: [], types: [], salaryKey: 'Tất cả' }); setPage(1) }

  const activeCount = (filters.locations?.length || 0) + (filters.levels?.length || 0) +
                      (filters.types?.length || 0) + (filters.salaryKey !== 'Tất cả' ? 1 : 0)

  return (
    <div className="animate-fade-in">
      <SectionHeader
        title="Tìm kiếm việc làm"
        subtitle="Khám phá cơ hội nghề nghiệp IT với AI"
      />

      <div className="flex gap-6">
        {/* Filter panel — desktop */}
        <div className="hidden lg:block w-56 shrink-0">
          <FilterPanel filters={filters} onChange={setFilter} onClear={clearFilters} />
        </div>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          {/* Mobile filter toggle */}
          <div className="flex items-center gap-3 mb-4 lg:hidden">
            <button
              onClick={() => setShowFilter(!showFilter)}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-200 rounded-lg text-sm text-text-secondary"
            >
              <Filter size={13} />
              Bộ lọc
              {activeCount > 0 && (
                <span className="ml-1 w-4 h-4 bg-indigo text-white text-2xs rounded-full flex items-center justify-center">
                  {activeCount}
                </span>
              )}
            </button>
          </div>

          {/* Mobile filter drawer */}
          {showFilter && (
            <div className="lg:hidden mb-4">
              <FilterPanel filters={filters} onChange={setFilter} onClear={clearFilters} />
            </div>
          )}

          {/* AI Banner */}
          <AIRecommendBanner />

          {/* Search Mode Toggle */}
          {queryParam && (
            <div className="mb-4 flex items-center gap-2 p-1.5 bg-gray-50 border border-gray-200 rounded-lg w-fit">
              <button
                onClick={() => setSearchMode('exact')}
                className={clsx(
                  "px-3 py-1.5 text-sm font-medium rounded-md transition-all",
                  searchMode === 'exact' ? "bg-white shadow-sm text-text-primary" : "text-text-secondary hover:text-text-primary"
                )}
              >
                🎯 Tìm chính xác
              </button>
              <button
                onClick={() => setSearchMode('semantic')}
                className={clsx(
                  "px-3 py-1.5 text-sm font-medium rounded-md transition-all flex items-center gap-1.5",
                  searchMode === 'semantic' ? "bg-white shadow-sm text-violet" : "text-text-secondary hover:text-violet"
                )}
              >
                <Sparkles size={14} /> Tìm bằng AI
              </button>
            </div>
          )}

          {/* Results header */}
          {searchError && (
            <div className="mb-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {searchError}
            </div>
          )}
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm text-text-secondary">
              {loading ? 'Đang tìm kiếm...' : (
                <><span className="font-semibold text-text-primary">{filtered.length}</span> kết quả{queryParam && <> cho &ldquo;<span className="text-violet">{queryParam}</span>&rdquo;</>}</>
              )}
            </p>
            {activeCount > 0 && (
              <button onClick={clearFilters} className="text-xs text-red-500 hover:underline">
                Xoá bộ lọc ({activeCount})
              </button>
            )}
          </div>

          {/* Job cards grid */}
          <div className="space-y-3">
            {loading
              ? Array(4).fill(0).map((_, i) => <JobCardSkeleton key={i} />)
              : filtered.length === 0
              ? <EmptyState icon="🔍" title="Không tìm thấy kết quả" description="Thử điều chỉnh bộ lọc hoặc tìm kiếm với từ khoá khác." action={<Button onClick={clearFilters} variant="secondary" size="sm">Xoá bộ lọc</Button>} />
              : paginated.map(job => <JobCard key={job.id} job={job} />)
            }
          </div>

          {/* Load more */}
          {!loading && hasMore && (
            <div className="mt-5 flex justify-center">
              <Button
                variant="secondary"
                onClick={() => setPage(p => p + 1)}
              >
                Load More Jobs <ChevronDown size={14} />
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
