import { Navigate, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { isAuthenticated, getCurrentUser } from '../lib/api'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation()
  const [loading, setLoading] = useState(true)
  const [mustChangePassword, setMustChangePassword] = useState(false)

  useEffect(() => {
    const checkUser = async () => {
      if (!isAuthenticated()) {
        setLoading(false)
        return
      }

      try {
        const user = await getCurrentUser()
        setMustChangePassword(user.must_change_password || false)
      } catch (error) {
        console.error('Failed to get user:', error)
      } finally {
        setLoading(false)
      }
    }

    checkUser()
  }, [])

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Laden...</div>
      </div>
    )
  }

  // Redirect to change password if required (but not if already on that page)
  if (mustChangePassword && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />
  }

  return <>{children}</>
}
