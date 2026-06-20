import { createContext, useContext, useState, useCallback } from 'react'
import { MOCK_JOBS, MOCK_PROFILE } from '../data/mockData'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [jobs, setJobs]       = useState(MOCK_JOBS)
  const [profile, setProfile] = useState(MOCK_PROFILE)
  const [notifications, setNotifications] = useState(3)

  // Toggle bookmark on a job
  const toggleSaved = useCallback((jobId) => {
    setJobs(prev =>
      prev.map(j => j.id === jobId ? { ...j, saved: !j.saved } : j)
    )
  }, [])

  // Update profile fields
  const updateProfile = useCallback((patch) => {
    setProfile(prev => ({ ...prev, ...patch }))
  }, [])

  const savedJobs = jobs.filter(j => j.saved)

  return (
    <AppContext.Provider value={{
      jobs, setJobs,
      savedJobs,
      toggleSaved,
      profile, updateProfile,
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
