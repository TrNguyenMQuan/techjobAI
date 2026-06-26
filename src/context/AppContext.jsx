import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { MOCK_JOBS, MOCK_PROFILE } from '../data/mockData'
import { useAuth } from './AuthContext'

const AppContext = createContext(null)

// ── localStorage helpers ───────────────────────────────────────────────────────
function sKey(base, uid) { return `techjob_${base}_${uid || 'guest'}` }

function loadJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function hasStoredValue(key) {
  return localStorage.getItem(key) !== null
}

function saveJSON(key, value) {
  localStorage.setItem(key, JSON.stringify(value))
}

function createFreshProfile(user) {
  const isDemoUser = user?.email === 'demo@techjob.ai'
  if (!user || isDemoUser) return { ...MOCK_PROFILE, onboardingCompleted: true }

  return {
    ...MOCK_PROFILE,
    name: user.name || '',
    title: '',
    email: user.email || '',
    phone: '',
    location: '',
    nationality: '',
    gender: '',
    dob: '',
    about: '',
    socialLinks: {
      facebook: '',
      github: '',
      linkedin: '',
      website: '',
    },
    completeness: 20,
    completenessHint: 'Complete your personal information to unlock the dashboard',
    skills: [],
    preferences: {
      ...MOCK_PROFILE.preferences,
      position: '',
      locations: [],
      workTypes: [],
    },
    onboardingCompleted: false,
  }
}

function buildProfileForUser(user, storedProfile, hasStoredProfile) {
  const isDemoUser = user?.email === 'demo@techjob.ai'
  const hasStoredOnboarding = storedProfile
    ? Object.prototype.hasOwnProperty.call(storedProfile, 'onboardingCompleted')
    : false

  const baseProfile = hasStoredProfile
    ? { ...MOCK_PROFILE, ...storedProfile }
    : createFreshProfile(user)

  if (user) {
    const shouldUseAuthName =
      !hasStoredProfile || !baseProfile.name || baseProfile.name === MOCK_PROFILE.name
    const shouldUseAuthEmail =
      !hasStoredProfile || !baseProfile.email || baseProfile.email === MOCK_PROFILE.email

    if (shouldUseAuthName) baseProfile.name = user.name
    if (shouldUseAuthEmail) baseProfile.email = user.email
    if (!hasStoredOnboarding) baseProfile.onboardingCompleted = isDemoUser
  }

  return baseProfile
}

// ── Provider ────────────────────────────────────────────────────────────────────
export function AppProvider({ children }) {
  const { user } = useAuth()
  const userId = user?.id || 'guest'

  const [jobs, setJobs]                     = useState(MOCK_JOBS)
  const [savedJobIds, setSavedJobIds]       = useState(new Set())
  const [savedJobs, setSavedJobs]           = useState([])
  const [profile, setProfile]               = useState(MOCK_PROFILE)
  const [profileOwnerId, setProfileOwnerId] = useState(null)
  const [cvFiles, setCvFiles]               = useState([])
  const [settings, setSettings]             = useState({
    semanticSearch: true, salaryEstimate: true,
    language: 'vi', timezone: 'Asia/Ho_Chi_Minh',
    notifEmail: true, notifJobAlert: true, notifWeekly: false,
  })
  const [notifications, setNotifications]   = useState(3)

  // ── Reload user-specific data when userId changes ──────────────────────────
  useEffect(() => {
    const profileKey = sKey('profile', userId)
    const hasStoredProfile = hasStoredValue(profileKey)
    const storedProfile = loadJSON(profileKey, null)
    const nextProfile = buildProfileForUser(user, storedProfile, hasStoredProfile)

    setSavedJobIds(new Set(loadJSON(sKey('saved_ids', userId), [])))
    setSavedJobs(loadJSON(sKey('saved_jobs', userId), []))
    setProfile(nextProfile)
    setProfileOwnerId(userId)
    saveJSON(profileKey, nextProfile)
    setCvFiles(loadJSON(sKey('cv_files', userId), []))
    setSettings(prev => loadJSON(sKey('settings', userId), prev))
  }, [user, userId])

  // ── Check if a job is saved ────────────────────────────────────────────────
  const isJobSaved = useCallback((jobId) => savedJobIds.has(String(jobId)), [savedJobIds])

  // ── Toggle bookmark on a job ───────────────────────────────────────────────
  const toggleSaved = useCallback((jobId, jobData) => {
    const id = String(jobId)

    setSavedJobIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      saveJSON(sKey('saved_ids', userId), [...next])
      return next
    })

    setSavedJobs(prev => {
      let next
      if (prev.some(j => String(j.id) === id)) {
        next = prev.filter(j => String(j.id) !== id)
      } else if (jobData) {
        next = [...prev, {
          id, title: jobData.title, company: jobData.company,
          companyInitial: jobData.companyInitial, companyColor: jobData.companyColor,
          location: jobData.location, type: jobData.type, level: jobData.level,
          salaryDisplay: jobData.salaryDisplay, salaryRaw: jobData.salaryRaw,
          aiEstimatedSalary: jobData.aiEstimatedSalary, skills: jobData.skills,
          postedDate: jobData.postedDate, saved: true,
        }]
      } else { next = prev }
      saveJSON(sKey('saved_jobs', userId), next)
      return next
    })
  }, [userId])

  // ── Update profile fields (persisted) ──────────────────────────────────────
  const updateProfile = useCallback((patch) => {
    setProfile(prev => {
      const updated = { ...prev, ...patch }
      saveJSON(sKey('profile', userId), updated)
      return updated
    })
  }, [userId])

  // ── CV file management (persisted) ─────────────────────────────────────────
  const addCvFile = useCallback((info) => {
    setCvFiles(prev => {
      const updated = [...prev, info]
      saveJSON(sKey('cv_files', userId), updated)
      return updated
    })
  }, [userId])

  const removeCvFile = useCallback((index) => {
    setCvFiles(prev => {
      const updated = prev.filter((_, i) => i !== index)
      saveJSON(sKey('cv_files', userId), updated)
      return updated
    })
  }, [userId])

  const setActiveCv = useCallback((index) => {
    setCvFiles(prev => {
      const updated = prev.map((f, i) => ({ ...f, active: i === index }))
      saveJSON(sKey('cv_files', userId), updated)
      return updated
    })
  }, [userId])

  // ── Update settings (persisted) ────────────────────────────────────────────
  const updateSettings = useCallback((patch) => {
    setSettings(prev => {
      const updated = { ...prev, ...patch }
      saveJSON(sKey('settings', userId), updated)
      return updated
    })
  }, [userId])

  return (
    <AppContext.Provider value={{
      jobs, setJobs,
      savedJobs, isJobSaved, toggleSaved,
      profile, updateProfile, profileReady: profileOwnerId === userId,
      cvFiles, addCvFile, removeCvFile, setActiveCv,
      settings, updateSettings,
      notifications, setNotifications,
    }}>
      {children}
    </AppContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}
