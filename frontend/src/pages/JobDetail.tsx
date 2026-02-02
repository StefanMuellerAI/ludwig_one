import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { Download, FileText, XCircle, CheckCircle, AlertCircle, Clock, ArrowLeft, RefreshCw, Eye } from 'lucide-react'
import { getJob, downloadArchive, downloadInsight, getInsightXml, cancelJob } from '../lib/api'
import { formatDate, getStatusColor } from '../lib/utils'
import { useState } from 'react'
import Dialog from '../components/Dialog'

export default function JobDetail() {
  const { jobId } = useParams<{ jobId: string }>()
  const queryClient = useQueryClient()
  const [showXmlDialog, setShowXmlDialog] = useState(false)
  const [xmlContent, setXmlContent] = useState('')
  const [loadingXml, setLoadingXml] = useState(false)

  const { data: job, isLoading, error } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => getJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      // Refetch every 3 seconds if processing
      return query.state.data?.status === 'processing' ? 3000 : false
    },
  })

  const cancelMutation = useMutation({
    mutationFn: () => cancelJob(jobId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', jobId] })
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
  })

  const handleShowXml = async () => {
    setLoadingXml(true)
    try {
      const xml = await getInsightXml(jobId!)
      setXmlContent(xml)
      setShowXmlDialog(true)
    } catch (error) {
      console.error('Failed to load XML:', error)
      alert('Fehler beim Laden des XML-Berichts')
    } finally {
      setLoadingXml(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <RefreshCw className="w-8 h-8 text-brand-600 animate-spin" />
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Fehler beim Laden der Auftragsdetails</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <Link
          to="/jobs"
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Zurück zu den Aufträgen
        </Link>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{job.original_filename}</h1>
              <p className="mt-1 text-sm text-gray-500">
                Auftrags-ID: {job.id}
              </p>
            </div>
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(job.status)}`}
            >
              {job.status === 'completed' ? 'ABGESCHLOSSEN' :
               job.status === 'processing' ? 'IN BEARBEITUNG' :
               job.status === 'failed' ? 'FEHLGESCHLAGEN' :
               job.status === 'pending' ? 'AUSSTEHEND' :
               job.status === 'cancelled' ? 'ABGEBROCHEN' :
               job.status.toUpperCase()}
            </span>
          </div>
        </div>

        <div className="px-6 py-5 space-y-6">
          {/* Progress */}
          {job.status === 'processing' && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Verarbeitungsfortschritt</span>
                <span className="text-sm font-medium text-brand-600">
                  {job.processed_files} / {job.total_files} Dateien
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-brand-600 h-3 rounded-full transition-all duration-500"
                  style={{
                    width: `${job.total_files > 0 ? (job.processed_files / job.total_files) * 100 : 0}%`,
                  }}
                ></div>
              </div>
              <p className="mt-2 text-sm text-gray-500">
                {job.total_files > 0
                  ? Math.round((job.processed_files / job.total_files) * 100)
                  : 0}% abgeschlossen
              </p>
            </div>
          )}

          {/* Details */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-500">Auftragstyp</h3>
              <p className="mt-1 text-sm text-gray-900">
                {job.type === 'pdf_splitting' ? 'PDF-Aufteilung' : 'TAR-Verarbeitung'}
              </p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Erstellt</h3>
              <p className="mt-1 text-sm text-gray-900">{formatDate(job.created_at)}</p>
            </div>
            {job.processing_started_at && (
              <div>
                <h3 className="text-sm font-medium text-gray-500">Gestartet</h3>
                <p className="mt-1 text-sm text-gray-900">{formatDate(job.processing_started_at)}</p>
              </div>
            )}
            {job.processing_completed_at && (
              <div>
                <h3 className="text-sm font-medium text-gray-500">Abgeschlossen</h3>
                <p className="mt-1 text-sm text-gray-900">{formatDate(job.processing_completed_at)}</p>
              </div>
            )}
            <div>
              <h3 className="text-sm font-medium text-gray-500">Dateien gesamt</h3>
              <p className="mt-1 text-sm text-gray-900">{job.total_files}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Verarbeitete Dateien</h3>
              <p className="mt-1 text-sm text-gray-900">{job.processed_files}</p>
            </div>
            {job.failed_files > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500">Fehlgeschlagene Dateien</h3>
                <p className="mt-1 text-sm text-red-600 font-medium">{job.failed_files}</p>
              </div>
            )}
          </div>

          {/* Error Message */}
          {job.error_message && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Fehler</h3>
                  <p className="mt-1 text-sm text-red-700">{job.error_message}</p>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            {job.status === 'completed' && (
              <>
                <button
                  onClick={() => downloadArchive(job.id)}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-brand-600 hover:bg-brand-700"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Archiv herunterladen
                </button>
                <button
                  onClick={() => downloadInsight(job.id)}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Bericht herunterladen
                </button>
                <button
                  onClick={handleShowXml}
                  disabled={loadingXml}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  <Eye className="w-4 h-4 mr-2" />
                  {loadingXml ? 'Lädt...' : 'XML anzeigen'}
                </button>
              </>
            )}

            {job.status === 'processing' && (
              <button
                onClick={() => cancelMutation.mutate()}
                disabled={cancelMutation.isPending}
                className="inline-flex items-center px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 disabled:opacity-50"
              >
                <XCircle className="w-4 h-4 mr-2" />
                {cancelMutation.isPending ? 'Wird abgebrochen...' : 'Auftrag abbrechen'}
              </button>
            )}
          </div>

          {/* Status Messages */}
          {job.status === 'completed' && (
            <div className="bg-green-50 border border-green-200 rounded-md p-4">
              <div className="flex">
                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">Verarbeitung abgeschlossen</h3>
                  <p className="mt-1 text-sm text-green-700">
                    Ihre Dokumente wurden verarbeitet und stehen zum Download bereit.
                  </p>
                </div>
              </div>
            </div>
          )}

          {job.status === 'processing' && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="flex">
                <Clock className="w-5 h-5 text-blue-400 flex-shrink-0 animate-pulse" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">In Bearbeitung...</h3>
                  <p className="mt-1 text-sm text-blue-700">
                    Ihre Dokumente werden verarbeitet. Diese Seite wird automatisch aktualisiert.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* XML Dialog */}
      <Dialog
        isOpen={showXmlDialog}
        onClose={() => setShowXmlDialog(false)}
        title="XML-Bericht"
      >
        <div className="overflow-auto max-h-[60vh]">
          <pre className="text-xs font-mono bg-gray-50 p-4 rounded border border-gray-200 whitespace-pre-wrap break-words">
            {xmlContent}
          </pre>
        </div>
      </Dialog>
    </div>
  )
}
