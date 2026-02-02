import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { FileArchive, FileText, RefreshCw } from 'lucide-react'
import { getJobs } from '../lib/api'
import { formatDate, getStatusColor } from '../lib/utils'

export default function Jobs() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => getJobs(0, 7), // Only show last 7 jobs
    refetchInterval: 5000, // Refetch every 5 seconds
  })

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <RefreshCw className="w-8 h-8 text-brand-600 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Fehler beim Laden der Aufträge</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Verarbeitungsaufträge</h1>
          <p className="mt-2 text-sm text-gray-600">
            Zeigt die letzten 7 Aufträge
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Aktualisieren
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden rounded-lg">
        {!data?.jobs || data.jobs.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Keine Aufträge</h3>
            <p className="mt-1 text-sm text-gray-500">Laden Sie ein Dokument hoch, um zu beginnen.</p>
            <div className="mt-6">
              <Link
                to="/upload"
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-brand-600 hover:bg-brand-700"
              >
                Dokument hochladen
              </Link>
            </div>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {data.jobs.map((job) => (
              <li key={job.id}>
                <Link
                  to={`/jobs/${job.id}`}
                  className="block hover:bg-gray-50 transition"
                >
                  <div className="px-6 py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        {job.type === 'pdf_splitting' ? (
                          <FileText className="w-8 h-8 text-red-500 flex-shrink-0" />
                        ) : (
                          <FileArchive className="w-8 h-8 text-blue-500 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {job.original_filename}
                          </p>
                          <p className="text-sm text-gray-500">
                            {job.type === 'pdf_splitting' ? 'PDF-Aufteilung' : 'TAR-Verarbeitung'}
                          </p>
                        </div>
                      </div>
                      <div className="ml-4 flex items-center space-x-4 flex-shrink-0">
                        <div className="text-right">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}
                          >
                            {job.status === 'completed' ? 'ABGESCHLOSSEN' :
                             job.status === 'processing' ? 'IN BEARBEITUNG' :
                             job.status === 'failed' ? 'FEHLGESCHLAGEN' :
                             job.status === 'pending' ? 'AUSSTEHEND' :
                             job.status === 'cancelled' ? 'ABGEBROCHEN' :
                             job.status.toUpperCase()}
                          </span>
                          <p className="text-xs text-gray-500 mt-1">
                            {job.processed_files}/{job.total_files} Dateien
                          </p>
                        </div>
                        <div className="text-right text-sm text-gray-500">
                          {formatDate(job.created_at)}
                        </div>
                      </div>
                    </div>

                    {job.status === 'processing' && (
                      <div className="mt-3">
                        <div className="relative pt-1">
                          <div className="flex mb-2 items-center justify-between">
                            <div>
                              <span className="text-xs font-semibold inline-block text-brand-600">
                                In Bearbeitung...
                              </span>
                            </div>
                            <div className="text-right">
                              <span className="text-xs font-semibold inline-block text-brand-600">
                                {job.total_files > 0
                                  ? Math.round((job.processed_files / job.total_files) * 100)
                                  : 0}
                                %
                              </span>
                            </div>
                          </div>
                          <div className="overflow-hidden h-2 text-xs flex rounded bg-brand-200">
                            <div
                              style={{
                                width: `${
                                  job.total_files > 0
                                    ? (job.processed_files / job.total_files) * 100
                                    : 0
                                }%`,
                              }}
                              className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-brand-500 transition-all duration-500"
                            ></div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
