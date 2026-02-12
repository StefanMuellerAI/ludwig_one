import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Upload as UploadIcon, FileArchive, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { uploadTarArchive, uploadPdf } from '../lib/api'
import ConfirmDialog from '../components/ConfirmDialog'

export default function Upload() {
  const navigate = useNavigate()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [showInvalidFileDialog, setShowInvalidFileDialog] = useState(false)

  const isArchiveFile = (name: string) => {
    const lower = name.toLowerCase()
    return lower.endsWith('.tar') || lower.endsWith('.tar.gz') || lower.endsWith('.tgz') || lower.endsWith('.zip')
  }

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      if (file.name.toLowerCase().endsWith('.pdf')) {
        return uploadPdf(file)
      } else {
        return uploadTarArchive(file)
      }
    },
    onSuccess: (data) => {
      navigate(`/jobs/${data.job_id}`)
    },
  })

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (file: File) => {
    const validExtensions = ['.tar', '.tar.gz', '.tgz', '.zip', '.pdf']
    const isValid = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext))

    if (!isValid) {
      setShowInvalidFileDialog(true)
      return
    }

    setSelectedFile(file)
  }

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile)
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-gray-900">Denkmalschutz-Steuerprüfung</h1>
        <p className="mt-3 text-lg text-gray-600">
          Prüfungssystem für Steuervergünstigungen bei Denkmalsanierungen
        </p>
      </div>

      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800">Relevante Dateien des Antragstellenden:</h2>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <div
          className={`border-2 border-dashed rounded-lg p-12 text-center ${
            dragActive ? 'border-brand-500 bg-brand-50' : 'border-gray-300'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-upload"
            className="hidden"
            accept=".tar,.tar.gz,.tgz,.zip,.pdf"
            onChange={handleChange}
          />

          {!selectedFile ? (
            <>
              <UploadIcon className="mx-auto h-12 w-12 text-gray-400" />
              <div className="mt-4">
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-brand-600 hover:bg-brand-700"
                >
                  Datei auswählen
                </label>
                <p className="mt-2 text-sm text-gray-500">oder per Drag & Drop</p>
              </div>
              <p className="mt-2 text-xs text-gray-500">
                TAR, TAR.GZ, TGZ, ZIP oder PDF bis zu 500MB
              </p>
            </>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-center text-green-600">
                <CheckCircle className="w-12 h-12" />
              </div>
              <div>
                <div className="flex items-center justify-center space-x-2">
                  {selectedFile.name.toLowerCase().endsWith('.pdf') ? (
                    <FileText className="w-5 h-5 text-red-500" />
                  ) : (
                    <FileArchive className="w-5 h-5 text-blue-500" />
                  )}
                  <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                </div>
                <p className="text-xs text-gray-500 mt-1">{formatBytes(selectedFile.size)}</p>
              </div>
              <div className="flex space-x-3 justify-center">
                <button
                  onClick={() => setSelectedFile(null)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Abbrechen
                </button>
                <button
                  onClick={handleUpload}
                  disabled={uploadMutation.isPending}
                  className="px-4 py-2 bg-brand-600 text-white rounded-md text-sm font-medium hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center"
                >
                  {uploadMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Wird hochgeladen...
                    </>
                  ) : (
                    'Hochladen & Verarbeiten'
                  )}
                </button>
              </div>
            </div>
          )}
        </div>

        {uploadMutation.isError && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md flex items-start">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Upload fehlgeschlagen</h3>
              <p className="text-sm text-red-700 mt-1">
                {uploadMutation.error instanceof Error ? uploadMutation.error.message : 'Unbekannter Fehler'}
              </p>
            </div>
          </div>
        )}

        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="border rounded-lg p-4">
            <div className="flex items-center">
              <FileArchive className="w-8 h-8 text-blue-500" />
              <h3 className="ml-3 text-lg font-medium text-gray-900">Archiv (TAR / ZIP)</h3>
            </div>
            <p className="mt-2 text-sm text-gray-600">
              Laden Sie ein TAR- oder ZIP-Archiv mit mehreren Dokumenten hoch. Jede Datei wird:
            </p>
            <ul className="mt-2 text-sm text-gray-600 list-disc list-inside space-y-1">
              <li>Automatisch kategorisiert</li>
              <li>Beschreibend umbenannt</li>
              <li>In Ordner organisiert</li>
              <li>Mit KI analysiert</li>
            </ul>
          </div>

          <div className="border rounded-lg p-4">
            <div className="flex items-center">
              <FileText className="w-8 h-8 text-red-500" />
              <h3 className="ml-3 text-lg font-medium text-gray-900">PDF-Dokument</h3>
            </div>
            <p className="mt-2 text-sm text-gray-600">
              Laden Sie eine PDF-Datei hoch. Das System wird:
            </p>
            <ul className="mt-2 text-sm text-gray-600 list-disc list-inside space-y-1">
              <li>In Seiten aufteilen</li>
              <li>Jede Seite kategorisieren</li>
              <li>Zusammenhängende Seiten intelligent zusammenführen</li>
              <li>Organisierte Dokumente erstellen</li>
            </ul>
          </div>
        </div>
      </div>

      <ConfirmDialog
        isOpen={showInvalidFileDialog}
        onClose={() => setShowInvalidFileDialog(false)}
        onConfirm={() => {}}
        title="Ungültiger Dateityp"
        message="Bitte laden Sie ein Archiv (.tar, .tar.gz, .tgz, .zip) oder eine PDF-Datei (.pdf) hoch."
        confirmText="OK"
        cancelText="Schließen"
        variant="warning"
      />
    </div>
  )
}
