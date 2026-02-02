import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Save, X } from 'lucide-react'
import { getCategories, createCategory, updateCategory, deleteCategory, Category } from '../lib/api'
import ConfirmDialog from '../components/ConfirmDialog'

export default function Categories() {
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [deleteDialog, setDeleteDialog] = useState<{ isOpen: boolean; categoryId: string; categoryName: string }>({
    isOpen: false,
    categoryId: '',
    categoryName: '',
  })
  const [formData, setFormData] = useState<Partial<Category>>({
    name: '',
    description: '',
    color: '#3B82F6',
    display_order: 0,
    is_active: true,
  })

  const { data: categories, isLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: () => getCategories(true),
  })

  const createMutation = useMutation({
    mutationFn: createCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      setIsCreating(false)
      resetForm()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Category> }) =>
      updateCategory(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      setEditingId(null)
      resetForm()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
    },
  })

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      color: '#3B82F6',
      display_order: 0,
      is_active: true,
    })
  }

  const handleEdit = (category: Category) => {
    setEditingId(category.id)
    setFormData(category)
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
    resetForm()
  }

  const handleDelete = (id: string, name: string) => {
    setDeleteDialog({ isOpen: true, categoryId: id, categoryName: name })
  }

  const confirmDelete = () => {
    deleteMutation.mutate(deleteDialog.categoryId)
    setDeleteDialog({ isOpen: false, categoryId: '', categoryName: '' })
  }

  if (isLoading) {
    return <div>Lädt...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Kategorien</h1>
          <p className="mt-2 text-sm text-gray-600">Dokumentenkategorien verwalten</p>
        </div>
        <button
          onClick={() => {
            setIsCreating(true)
            setEditingId(null)
            resetForm()
          }}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-brand-600 hover:bg-brand-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Kategorie hinzufügen
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Beschreibung
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Reihenfolge
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Aktiv
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Aktionen
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isCreating && (
              <tr className="bg-blue-50">
                <td className="px-6 py-4">
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    placeholder="Kategoriename"
                  />
                </td>
                <td className="px-6 py-4">
                  <input
                    type="text"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    placeholder="Beschreibung"
                  />
                </td>
                <td className="px-6 py-4">
                  <input
                    type="number"
                    value={formData.display_order}
                    onChange={(e) =>
                      setFormData({ ...formData, display_order: parseInt(e.target.value) })
                    }
                    className="block w-20 px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                </td>
                <td className="px-6 py-4">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="h-4 w-4 text-brand-600 border-gray-300 rounded"
                  />
                </td>
                <td className="px-6 py-4 text-right space-x-2">
                  <button
                    onClick={handleSave}
                    disabled={createMutation.isPending}
                    className="text-green-600 hover:text-green-900"
                  >
                    <Save className="w-5 h-5" />
                  </button>
                  <button onClick={handleCancel} className="text-gray-600 hover:text-gray-900">
                    <X className="w-5 h-5" />
                  </button>
                </td>
              </tr>
            )}

            {categories?.map((category) => (
              <tr key={category.id}>
                {editingId === category.id ? (
                  <>
                    <td className="px-6 py-4">
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <input
                        type="text"
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <input
                        type="number"
                        value={formData.display_order}
                        onChange={(e) =>
                          setFormData({ ...formData, display_order: parseInt(e.target.value) })
                        }
                        className="block w-20 px-3 py-2 border border-gray-300 rounded-md text-sm"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        checked={formData.is_active}
                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                        className="h-4 w-4 text-brand-600 border-gray-300 rounded"
                      />
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button
                        onClick={handleSave}
                        disabled={updateMutation.isPending}
                        className="text-green-600 hover:text-green-900"
                      >
                        <Save className="w-5 h-5" />
                      </button>
                      <button onClick={handleCancel} className="text-gray-600 hover:text-gray-900">
                        <X className="w-5 h-5" />
                      </button>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{category.name}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-500">{category.description}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{category.display_order}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          category.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {category.is_active ? 'Aktiv' : 'Inaktiv'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      <button
                        onClick={() => handleEdit(category)}
                        className="text-brand-600 hover:text-indigo-900"
                      >
                        <Edit2 className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(category.id, category.name)}
                        disabled={deleteMutation.isPending}
                        className="text-red-600 hover:text-red-900"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, categoryId: '', categoryName: '' })}
        onConfirm={confirmDelete}
        title="Kategorie löschen"
        message={`Möchten Sie die Kategorie "${deleteDialog.categoryName}" wirklich löschen?\n\nAlle Dokumente mit dieser Kategorie verlieren ihre Zuordnung.`}
        confirmText="Löschen"
        cancelText="Abbrechen"
        variant="danger"
      />
    </div>
  )
}
