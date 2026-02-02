import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { changePassword, removeToken } from '../lib/api'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Alert, AlertDescription } from '../components/ui/alert'
import { Lock, CheckCircle } from 'lucide-react'

export default function ChangePassword() {
  const navigate = useNavigate()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess(false)

    // Validation
    if (newPassword.length < 8) {
      setError('Neues Passwort muss mindestens 8 Zeichen lang sein')
      return
    }

    if (newPassword !== confirmPassword) {
      setError('Neue Passwörter stimmen nicht überein')
      return
    }

    setLoading(true)

    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
      })

      setSuccess(true)

      // Remove token and redirect to login after 2 seconds
      setTimeout(() => {
        removeToken()
        navigate('/login')
      }, 2000)
    } catch (err: any) {
      console.error('Password change error:', err)
      setError(
        err.response?.data?.detail ||
        'Passwort-Änderung fehlgeschlagen. Bitte überprüfen Sie Ihre Eingaben.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 to-brand-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-red-100 rounded-full flex items-center justify-center">
            <Lock className="h-8 w-8 text-red-600" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            Passwort ändern erforderlich
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Aus Sicherheitsgründen müssen Sie Ihr initiales Passwort ändern
          </p>
        </div>

        {/* Form */}
        <form className="mt-8 space-y-6 bg-white rounded-lg shadow-xl p-8" onSubmit={handleSubmit}>
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert className="bg-green-50 border-green-200">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                Passwort erfolgreich geändert! Sie werden zum Login weitergeleitet. Bitte melden Sie sich mit Ihrem neuen Passwort an.
              </AlertDescription>
            </Alert>
          )}

          <div className="space-y-4">
            <div>
              <Label htmlFor="current_password">Aktuelles Passwort</Label>
              <Input
                id="current_password"
                name="current_password"
                type="password"
                autoComplete="current-password"
                required
                value={currentPassword}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCurrentPassword(e.target.value)}
                disabled={loading || success}
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="new_password">Neues Passwort (min. 8 Zeichen)</Label>
              <Input
                id="new_password"
                name="new_password"
                type="password"
                autoComplete="new-password"
                required
                value={newPassword}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewPassword(e.target.value)}
                disabled={loading || success}
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="confirm_password">Neues Passwort bestätigen</Label>
              <Input
                id="confirm_password"
                name="confirm_password"
                type="password"
                autoComplete="new-password"
                required
                value={confirmPassword}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfirmPassword(e.target.value)}
                disabled={loading || success}
                className="mt-1"
              />
            </div>
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={loading || success}
          >
            {loading ? 'Wird geändert...' : success ? 'Erfolgreich!' : 'Passwort ändern'}
          </Button>

          <div className="text-center text-xs text-gray-500 mt-4">
            <p>Hinweise:</p>
            <ul className="mt-2 text-left list-disc list-inside space-y-1">
              <li>Mindestens 8 Zeichen</li>
              <li>Verwenden Sie ein sicheres Passwort</li>
              <li>Nicht das gleiche wie das aktuelle Passwort</li>
            </ul>
          </div>
        </form>
      </div>
    </div>
  )
}
