import { useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { useApp } from '../context/AppContext'

/** Keeps AppContext profile in sync with the authenticated user.
 *  Only syncs name/email when the user identity actually changes
 *  (login / register), not on every page reload. */
export default function SyncProfile() {
  const { user } = useAuth()
  const { updateProfile } = useApp()
  const prevUserId = useRef(null)

  useEffect(() => {
    if (user && user.id !== prevUserId.current) {
      // Only push auth name/email on actual identity change (login/register),
      // not on mount when restoring the same session.
      if (prevUserId.current !== null) {
        updateProfile({ name: user.name, email: user.email })
      }
      prevUserId.current = user.id
    } else if (!user) {
      prevUserId.current = null
    }
  }, [user, updateProfile])

  return null
}
