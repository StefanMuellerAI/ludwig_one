import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, CheckCircle } from 'lucide-react'
import { getPrompts, createPrompt, updatePrompt, deletePrompt, PromptTemplate } from '../lib/api'
import { PROMPT_PURPOSES, PROMPT_DEFAULTS } from '../lib/promptDefaults'
import ConfirmDialog from '../components/ConfirmDialog'

export default function Prompts() {
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [showPurposeSelector, setShowPurposeSelector] = useState(false)
  const [deleteDialog, setDeleteDialog] = useState<{ isOpen: boolean; promptId: string; promptName: string }>({
    isOpen: false,
    promptId: '',
    promptName: '',
  })
  const [formData, setFormData] = useState<Partial<PromptTemplate>>({
    name: '',
    purpose: '',
    template: '',
    model_name: 'mistral-large-latest',
    temperature: 0.1,
    max_tokens: 4096,
    is_active: true,
  })

  const { data: prompts, isLoading } = useQuery({
    queryKey: ['prompts'],
    queryFn: () => getPrompts(true),
  })

  // Get existing purposes to prevent duplicates
  const existingPurposes = useMemo(() => {
    return new Set(prompts?.map((p) => p.purpose) || [])
  }, [prompts])

  const createMutation = useMutation({
    mutationFn: createPrompt,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
      setIsCreating(false)
      resetForm()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<PromptTemplate> }) =>
      updatePrompt(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
      setEditingId(null)
      resetForm()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deletePrompt,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })

  const resetForm = () => {
    setFormData({
      name: '',
      purpose: '',
      template: '',
      model_name: 'mistral-large-latest',
      temperature: 0.1,
      max_tokens: 4096,
      is_active: true,
    })
  }

  const handleEdit = (prompt: PromptTemplate) => {
    setEditingId(prompt.id)
    setFormData(prompt)
    setIsCreating(false)
  }

  const handleSave = () => {
    if (isCreating) {
      createMutation.mutate(formData)
    } else if (editingId) {
      updateMutation.mutate({ id: editingId, data: formData })
    }
  }

  const handleCancel = () => {
    setEditingId(null)
    setIsCreating(false)
    setShowPurposeSelector(false)
    resetForm()
  }

  const handlePurposeSelect = (purpose: string) => {
    const defaults = PROMPT_DEFAULTS[purpose]
    if (defaults) {
      setFormData({
        ...defaults,
        is_active: true,
      })
    }
    setShowPurposeSelector(false)
    setIsCreating(true)
  }

  const handleDelete = (id: string, name: string) => {
    setDeleteDialog({ isOpen: true, promptId: id, promptName: name })
  }

  const confirmDelete = () => {
    deleteMutation.mutate(deleteDialog.promptId)
    setDeleteDialog({ isOpen: false, promptId: '', promptName: '' })
  }

  if (isLoading) {
    return <div>Lädt...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Prompt-Vorlagen</h1>
          <p className="mt-2 text-sm text-gray-600">LLM-Prompt-Vorlagen für Dokumentenverarbeitung verwalten</p>
        </div>
        <button
          onClick={() => {
            setShowPurposeSelector(true)
            setIsCreating(false)
            setEditingId(null)
            resetForm()
          }}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-brand-600 hover:bg-brand-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Prompt hinzufügen
        </button>
      </div>

      <div className="space-y-4">
        {showPurposeSelector && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-medium mb-4">Zweck auswählen</h3>
            <p className="text-sm text-gray-600 mb-4">
              Wählen Sie den Zweck des Prompts aus. Die Felder werden automatisch mit den Standard-Vorlagen vorbelegt.
              {existingPurposes.size > 0 && (
                <span className="block mt-1 text-xs">
                  Bereits vorhandene Zwecke sind markiert und können nicht dupliziert werden.
                </span>
              )}
            </p>
            <div className="grid grid-cols-2 gap-3">
              {PROMPT_PURPOSES.map((purpose) => {
                const isExisting = existingPurposes.has(purpose.value)
                return (
                  <button
                    key={purpose.value}
                    onClick={() => !isExisting && handlePurposeSelect(purpose.value)}
                    disabled={isExisting}
                    className={`text-left p-4 border rounded-lg transition-colors ${
                      isExisting
                        ? 'bg-gray-100 border-gray-300 cursor-not-allowed opacity-60'
                        : 'border-gray-300 hover:bg-white hover:border-brand-500'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-medium text-gray-900">{purpose.label}</div>
                      {isExisting && (
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                      )}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      <code>{purpose.value}</code>
                      {isExisting && <span className="ml-2 text-green-600 font-medium">✓ Vorhanden</span>}
                    </div>
                  </button>
                )
              })}
            </div>
            <div className="mt-4 flex justify-end">
              <button
                onClick={handleCancel}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Abbrechen
              </button>
            </div>
          </div>
        )}

        {isCreating && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-medium mb-4">
              Neuen Prompt erstellen
              <span className="ml-2 text-sm font-normal text-gray-600">
                (Zweck: <code className="bg-white px-2 py-1 rounded">{formData.purpose}</code>)
              </span>
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="z.B. Vision-Extraktion"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Zweck (nicht änderbar)</label>
                <input
                  type="text"
                  value={formData.purpose}
                  disabled
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-gray-100 cursor-not-allowed"
                />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Vorlage</label>
                <textarea
                  value={formData.template}
                  onChange={(e) => setFormData({ ...formData, template: e.target.value })}
                  rows={6}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
                  placeholder="Prompt-Vorlage mit {Platzhaltern}"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Modell</label>
                <select
                  value={formData.model_name}
                  onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="mistral-large-latest">Mistral Large</option>
                  <option value="mistral-medium-latest">Mistral Medium</option>
                  <option value="mistral-small-latest">Mistral Small</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Temperatur</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={formData.temperature}
                  onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max. Tokens</label>
                <input
                  type="number"
                  value={formData.max_tokens}
                  onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Token-Limit (Chunking)
                  <span className="ml-1 text-xs text-gray-500">(nur insight_generation)</span>
                </label>
                <input
                  type="number"
                  value={formData.token_limit || ''}
                  onChange={(e) => setFormData({ ...formData, token_limit: e.target.value ? parseInt(e.target.value) : undefined })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="100000 (Standard)"
                />
              </div>
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="h-4 w-4 text-brand-600 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">Aktiv</span>
                </label>
              </div>
            </div>
            <div className="mt-4 flex justify-end space-x-2">
              <button
                onClick={handleCancel}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Abbrechen
              </button>
              <button
                onClick={handleSave}
                disabled={createMutation.isPending}
                className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-brand-600 hover:bg-brand-700 disabled:opacity-50"
              >
                {createMutation.isPending ? 'Speichert...' : 'Speichern'}
              </button>
            </div>
          </div>
        )}

        {prompts?.map((prompt) => (
          <div key={prompt.id} className="bg-white border border-gray-200 rounded-lg">
            {editingId === prompt.id ? (
              <div className="p-6">
                <h3 className="text-lg font-medium mb-4">Prompt bearbeiten</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Zweck</label>
                    <input
                      type="text"
                      value={formData.purpose}
                      onChange={(e) => setFormData({ ...formData, purpose: e.target.value })}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Vorlage</label>
                    <textarea
                      value={formData.template}
                      onChange={(e) => setFormData({ ...formData, template: e.target.value })}
                      rows={6}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Modell</label>
                    <select
                      value={formData.model_name}
                      onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    >
                      <option value="mistral-large-latest">Mistral Large</option>
                      <option value="mistral-medium-latest">Mistral Medium</option>
                      <option value="mistral-small-latest">Mistral Small</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Temperatur</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      value={formData.temperature}
                      onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max. Tokens</label>
                    <input
                      type="number"
                      value={formData.max_tokens}
                      onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Token-Limit (Chunking)
                      <span className="ml-1 text-xs text-gray-500">(nur insight_generation)</span>
                    </label>
                    <input
                      type="number"
                      value={formData.token_limit || ''}
                      onChange={(e) => setFormData({ ...formData, token_limit: e.target.value ? parseInt(e.target.value) : undefined })}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      placeholder="100000 (Standard)"
                    />
                  </div>
                  <div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.is_active}
                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                        className="h-4 w-4 text-brand-600 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700">Aktiv</span>
                    </label>
                  </div>
                </div>
                <div className="mt-4 flex justify-end space-x-2">
                  <button
                    onClick={handleCancel}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Abbrechen
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={updateMutation.isPending}
                    className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-brand-600 hover:bg-brand-700 disabled:opacity-50"
                  >
                    {updateMutation.isPending ? 'Speichert...' : 'Speichern'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-6">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-semibold text-gray-900">{prompt.name}</h3>
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          prompt.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {prompt.is_active ? 'Aktiv' : 'Inaktiv'}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-gray-500">Zweck: <code className="bg-gray-100 px-2 py-1 rounded">{prompt.purpose}</code></p>
                    <div className="mt-3 p-3 bg-gray-50 rounded border border-gray-200">
                      <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">{prompt.template}</pre>
                    </div>
                    <div className="mt-3 flex space-x-6 text-sm text-gray-500">
                      <span>Modell: <strong>{prompt.model_name}</strong></span>
                      <span>Temp.: <strong>{prompt.temperature}</strong></span>
                      <span>Max. Tokens: <strong>{prompt.max_tokens}</strong></span>
                      {prompt.token_limit && (
                        <span>Token-Limit: <strong>{prompt.token_limit.toLocaleString()}</strong></span>
                      )}
                    </div>
                  </div>
                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={() => handleEdit(prompt)}
                      className="text-brand-600 hover:text-indigo-900"
                    >
                      <Edit2 className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleDelete(prompt.id, prompt.name)}
                      disabled={deleteMutation.isPending}
                      className="text-red-600 hover:text-red-900 disabled:opacity-50"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, promptId: '', promptName: '' })}
        onConfirm={confirmDelete}
        title="Prompt-Vorlage löschen"
        message={`Möchten Sie die Prompt-Vorlage "${deleteDialog.promptName}" wirklich löschen?\n\nWARNUNG: Wenn dies die einzige aktive Vorlage für diesen Zweck ist, kann das System diesen Workflow nicht mehr ausführen. Die Verarbeitung wird fehlschlagen.`}
        confirmText="Löschen"
        cancelText="Abbrechen"
        variant="danger"
      />
    </div>
  )
}
