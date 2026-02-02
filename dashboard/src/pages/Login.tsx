import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../lib/api'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Alert, AlertDescription } from '../components/ui/alert'
import { Lock, User } from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login({ username, password })
      navigate('/')
    } catch (err: any) {
      console.error('Login error:', err)
      setError(
        err.response?.data?.detail ||
        'Login fehlgeschlagen. Bitte überprüfen Sie Ihre Zugangsdaten.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 to-brand-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Logo */}
        <div className="text-center">
          <img
            src="/logo.png"
            alt="LudwigOne Logo"
            className="mx-auto h-24 w-auto"
          />
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            Admin Dashboard
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Melden Sie sich an, um fortzufahren
          </p>
        </div>

        {/* Login Form */}
        <form className="mt-8 space-y-6 bg-white rounded-lg shadow-xl p-8" onSubmit={handleSubmit}>
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-4">
            <div>
              <Label htmlFor="username">Benutzername</Label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <Input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={username}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUsername(e.target.value)}
                  className="pl-10"
                  placeholder="admin"
                  disabled={loading}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="password">Passwort</Label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                  className="pl-10"
                  placeholder="••••••••"
                  disabled={loading}
                />
              </div>
            </div>
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={loading}
          >
            {loading ? 'Anmeldung läuft...' : 'Anmelden'}
          </Button>

          <div className="text-center text-sm text-gray-500 mt-4">
            Standard Zugangsdaten: admin / admin123
          </div>
        </form>

        {/* Footer */}
        <div className="text-center text-xs text-gray-500">
          <p>LudwigOne © 2024</p>
        </div>
      </div>
    </div>
  )
}
