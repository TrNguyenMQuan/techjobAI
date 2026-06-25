import { useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useApp } from '../context/AppContext'

/** Keeps AppContext profile in sync with the authenticated user */
export default function SyncProfile() {
  const { user } = useAuth()
  const { updateProfile } = useApp()

  useEffect(() => {
    if (user) {
      updateProfile({ name: user.name, email: user.email })
    }
  }, [user, updateProfile])

  return null
}
