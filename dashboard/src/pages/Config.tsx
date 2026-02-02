import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, Eye, EyeOff } from 'lucide-react'
import { getConfig, updateConfig, SystemConfig } from '../lib/api'

export default function Config() {
  const queryClient = useQueryClient()
  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const [showSecrets, setShowSecrets] = useState(false)

  const { data: configs, isLoading } = useQuery({
    queryKey: ['config', showSecrets],
    queryFn: () => getConfig(showSecrets),
  })

  const updateMutation = useMutation({
    mutationFn: ({ key, value }: { key: string; value: string }) => updateConfig(key, value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] })
      setEditingKey(null)
      setEditValue('')
    },
  })

  const handleEdit = (config: SystemConfig) => {
    setEditingKey(config.key)
    setEditValue(config.value)
  }

  const handleSave = (key: string) => {
    updateMutation.mutate({ key, value: editValue })
  }

  const handleCancel = () => {
    setEditingKey(null)
    setEditValue('')
  }

  if (isLoading) {
    return <div>Lädt...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Konfiguration</h1>
          <p className="mt-2 text-sm text-gray-600">Systemkonfiguration und Einstellungen</p>
        </div>
        <button
          onClick={() => setShowSecrets(!showSecrets)}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          {showSecrets ? (
            <>
              <EyeOff className="w-4 h-4 mr-2" />
              Sensible Daten verbergen
            </>
          ) : (
            <>
              <Eye className="w-4 h-4 mr-2" />
              Sensible Daten anzeigen
            </>
          )}
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Schlüssel
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Wert
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Typ
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Beschreibung
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Aktionen
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {configs?.map((config) => (
              <tr key={config.key} className={config.is_secret ? 'bg-yellow-50' : ''}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="text-sm font-medium text-gray-900">{config.key}</div>
                    {config.is_secret && (
                      <span className="ml-2 px-2 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">
                        Sensibel
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  {editingKey === config.key ? (
                    <input
                      type={config.is_secret && !showSecrets ? 'password' : 'text'}
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  ) : (
                    <div className="text-sm text-gray-900">
                      {config.value === '***MASKED***' ? (
                        <span className="text-gray-400 italic">***MASKIERT***</span>
                      ) : config.value_type === 'boolean' ? (
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            config.value === 'true'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {config.value}
                        </span>
                      ) : (
                        config.value
                      )}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">{config.value_type}</div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-500">{config.description}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  {editingKey === config.key ? (
                    <div className="space-x-2">
                      <button
                        onClick={() => handleSave(config.key)}
                        disabled={updateMutation.isPending}
                        className="text-green-600 hover:text-green-900"
                      >
                        <Save className="w-5 h-5 inline" />
                      </button>
                      <button
                        onClick={handleCancel}
                        className="text-gray-600 hover:text-gray-900"
                      >
                        Abbrechen
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => handleEdit(config)}
                      className="text-brand-600 hover:text-indigo-900"
                    >
                      Bearbeiten
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-800">Konfigurationshinweise</h3>
        <ul className="mt-2 text-sm text-blue-700 list-disc list-inside space-y-1">
          <li>Änderungen an der Konfiguration werden sofort wirksam</li>
          <li>Sensible Werte sind standardmäßig maskiert - Klicken Sie auf "Sensible Daten anzeigen"</li>
          <li>E-Mail-Einstellungen erfordern gültige SMTP-Zugangsdaten</li>
          <li>Starten Sie die Worker nach Änderung der LLM-Provider-Einstellungen neu</li>
        </ul>
      </div>
    </div>
  )
}
