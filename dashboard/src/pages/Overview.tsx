import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, CheckCircle, XCircle, Clock, Trash2 } from 'lucide-react'
import { getJobs, getCategories, deleteJob } from '../lib/api'
import { formatDate } from '../lib/utils'
import ConfirmDialog from '../components/ConfirmDialog'

export default function Overview() {
  const queryClient = useQueryClient()
  const [deleteDialog, setDeleteDialog] = useState<{ isOpen: boolean; jobId: string; filename: string }>({
    isOpen: false,
    jobId: '',
    filename: '',
  })

  const { data: jobsData } = useQuery({
    queryKey: ['jobs'],
    queryFn: getJobs,
    refetchInterval: 10000,
  })

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => getCategories(false),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
  })

  const handleDelete = (jobId: string, filename: string) => {
    setDeleteDialog({ isOpen: true, jobId, filename })
  }

  const confirmDelete = () => {
    deleteMutation.mutate(deleteDialog.jobId)
    setDeleteDialog({ isOpen: false, jobId: '', filename: '' })
  }

  const jobs = jobsData?.jobs || []
  const totalJobs = jobsData?.total || 0

  const completedJobs = jobs.filter((j) => j.status === 'completed').length
  const processingJobs = jobs.filter((j) => j.status === 'processing').length
  const failedJobs = jobs.filter((j) => j.status === 'failed').length

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Übersicht</h1>
        <p className="mt-2 text-sm text-gray-600">Systemstatus und aktuelle Aktivitäten</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FileText className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Aufträge gesamt</dt>
                  <dd className="text-3xl font-semibold text-gray-900">{totalJobs}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircle className="h-6 w-6 text-green-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Abgeschlossen</dt>
                  <dd className="text-3xl font-semibold text-gray-900">{completedJobs}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Clock className="h-6 w-6 text-blue-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">In Bearbeitung</dt>
                  <dd className="text-3xl font-semibold text-gray-900">{processingJobs}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <XCircle className="h-6 w-6 text-red-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Fehlgeschlagen</dt>
                  <dd className="text-3xl font-semibold text-gray-900">{failedJobs}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* All Jobs Table */}
      <div className="bg-white shadow rounded-lg mb-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Alle Aufträge</h2>
        </div>
        <div className="overflow-x-auto">
          {jobs.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">Noch keine Aufträge vorhanden</p>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Dateiname
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Typ
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fortschritt
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Erstellt
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Aktionen
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {jobs.map((job) => (
                  <tr key={job.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {job.original_filename}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {job.type === 'pdf_splitting' ? 'PDF' : 'TAR'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${
                          job.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : job.status === 'processing'
                            ? 'bg-blue-100 text-blue-800'
                            : job.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {job.status === 'completed' ? 'abgeschlossen' :
                         job.status === 'processing' ? 'in Bearbeitung' :
                         job.status === 'failed' ? 'fehlgeschlagen' :
                         job.status === 'pending' ? 'ausstehend' :
                         job.status === 'cancelled' ? 'abgebrochen' :
                         job.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {job.processed_files}/{job.total_files}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(job.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleDelete(job.id, job.original_filename)}
                        disabled={deleteMutation.isPending}
                        className="text-red-600 hover:text-red-900 disabled:opacity-50"
                        title="Auftrag löschen"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Categories */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Kategorien</h2>
          </div>
          <div className="p-6">
            {!categories || categories.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">Keine Kategorien vorhanden</p>
            ) : (
              <div className="space-y-3">
                {categories.map((category) => (
                  <div key={category.id} className="flex items-center">
                    <div
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: category.color || '#6B7280' }}
                    ></div>
                    <span className="ml-3 text-sm text-gray-900">{category.name}</span>
                    {!category.is_active && (
                      <span className="ml-2 text-xs text-gray-500">(inaktiv)</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, jobId: '', filename: '' })}
        onConfirm={confirmDelete}
        title="Auftrag löschen"
        message={`Möchten Sie den Auftrag "${deleteDialog.filename}" wirklich löschen?\n\nDadurch werden alle zugehörigen Daten (Dokumente, Extraktionen, etc.) dauerhaft entfernt.`}
        confirmText="Löschen"
        cancelText="Abbrechen"
        variant="danger"
      />
    </div>
  )
}
