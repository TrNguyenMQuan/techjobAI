import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useApp } from '../context/AppContext'

export default function ProtectedRoute({ children, allowIncompleteProfile = false }) {
  const { isAuthenticated, loading } = useAuth()
  const { profile, profileReady } = useApp()
  const location = useLocation()

  if (loading || (isAuthenticated && !profileReady)) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo flex items-center justify-center animate-pulse">
            <span className="text-white text-sm font-black">T</span>
          </div>
          <p className="text-sm text-text-secondary">Đang tải...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (!allowIncompleteProfile && profile?.onboardingCompleted === false) {
    return <Navigate to="/onboarding" state={{ from: location }} replace />
  }

  return children
}
