import { useState, useEffect, useMemo, useCallback } from 'react'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { getJobs } from '../services/jobService'
import { getProfile, updateProfile as updateProfileApi } from '../services/profileService'

/**
 * Debounce a fast-changing value (e.g. a search input) so we don't re-filter
 * or re-fetch on every keystroke.
 */
export function useDebounce(value, delay = 350) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
}

/**
 * FR-1/FR-5 — Job search + filter state management.
 * Wraps React Query so list results are cached and refetched automatically
 * when filters change; UI components only need `jobs`, `isLoading`, `setFilter`.
 */
export function useJobSearch(initialFilters = {}) {
  const [filters, setFilters] = useState({
    locations: [], levels: [], types: [], salaryKey: 'Tất cả', ...initialFilters,
  })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['jobs', filters],
    queryFn: () => getJobs(filters),
    placeholderData: keepPreviousData,
  })

  const setFilter = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }, [])

  const clearFilters = useCallback(() => {
    setFilters({ locations: [], levels: [], types: [], salaryKey: 'Tất cả' })
  }, [])

  const activeCount = useMemo(() => (
    (filters.locations?.length || 0) +
    (filters.levels?.length || 0) +
    (filters.types?.length || 0) +
    (filters.salaryKey !== 'Tất cả' ? 1 : 0)
  ), [filters])

  return {
    jobs: data?.data || [],
    total: data?.total || 0,
    isLoading, isError, refetch,
    filters, setFilter, clearFilters, activeCount,
  }
}

/** FR-4 — Profile state, backed by React Query for caching + refetch. */
export function useProfile() {
  const { data: profile, isLoading, refetch } = useQuery({
    queryKey: ['profile'],
    queryFn: getProfile,
  })

  const save = useCallback(async (patch) => {
    const updated = await updateProfileApi(patch)
    refetch()
    return updated
  }, [refetch])

  return { profile, isLoading, save, refetch }
}
