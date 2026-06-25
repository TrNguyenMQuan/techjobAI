import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import * as authService from '../services/authService'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]         = useState(null)
  const [loading, setLoading]   = useState(true)

  const refreshUser = useCallback(async () => {
    try {
      const current = await authService.getCurrentUser()
      setUser(current)
      return current
    } catch {
      authService.clearStoredToken()
      setUser(null)
      return null
    }
  }, [])

  useEffect(() => {
    refreshUser().finally(() => setLoading(false))
  }, [refreshUser])

  const login = useCallback(async (credentials) => {
    const { user: loggedIn } = await authService.login(credentials)
    setUser(loggedIn)
    return loggedIn
  }, [])

  const register = useCallback(async (data) => {
    const { user: registered } = await authService.register(data)
    setUser(registered)
    return registered
  }, [])

  const logout = useCallback(async () => {
    await authService.logout()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      loading,
      login,
      register,
      logout,
      refreshUser,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
