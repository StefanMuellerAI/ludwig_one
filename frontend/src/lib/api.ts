import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''
const API_KEY = import.meta.env.VITE_API_KEY || ''

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  if (API_KEY) {
    config.headers = config.headers || {}
    config.headers['X-API-Key'] = API_KEY
  }
  return config
})

export interface Job {
  id: string
  type: string
  status: string
  workflow_id?: string
  total_files: number
  processed_files: number
  failed_files: number
  original_filename: string
  output_archive_path?: string
  error_message?: string
  processing_started_at?: string
  processing_completed_at?: string
  created_at: string
  updated_at: string
}

export interface JobListResponse {
  jobs: Job[]
  total: number
}

export interface JobCreateResponse {
  job_id: string
  message: string
}

// Upload TAR archive
export const uploadTarArchive = async (file: File): Promise<JobCreateResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post<JobCreateResponse>('/api/v1/jobs/tar-upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

// Upload PDF
export const uploadPdf = async (file: File): Promise<JobCreateResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post<JobCreateResponse>('/api/v1/jobs/pdf-upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

// Get all jobs
export const getJobs = async (skip = 0, limit = 100): Promise<JobListResponse> => {
  const response = await api.get<JobListResponse>('/api/v1/jobs', {
    params: { skip, limit },
  })

  return response.data
}

// Get job by ID
export const getJob = async (jobId: string): Promise<Job> => {
  const response = await api.get<Job>(`/api/v1/jobs/${jobId}`)
  return response.data
}

// Download result archive
const extractFilename = (contentDisposition?: string | null): string | null => {
  if (!contentDisposition) return null
  const match = contentDisposition.match(/filename=([^;]+)/i)
  return match ? match[1].replace(/"/g, '').trim() : null
}

const downloadBlob = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

// Download result archive
export const downloadArchive = async (jobId: string) => {
  const response = await api.get(`/api/v1/jobs/${jobId}/download`, {
    responseType: 'blob',
  })
  const filename =
    extractFilename(response.headers['content-disposition']) || `job_${jobId}_result.tar`
  downloadBlob(response.data, filename)
}

// Download insight XML
export const downloadInsight = async (jobId: string) => {
  const response = await api.get(`/api/v1/jobs/${jobId}/insight`, {
    responseType: 'blob',
  })
  const filename =
    extractFilename(response.headers['content-disposition']) || `insight_${jobId}.xml`
  downloadBlob(response.data, filename)
}

// Get insight XML as text
export const getInsightXml = async (jobId: string): Promise<string> => {
  const response = await api.get(`/api/v1/jobs/${jobId}/insight`, {
    responseType: 'text',
  })
  return response.data
}

// Cancel job
export const cancelJob = async (jobId: string): Promise<void> => {
  await api.delete(`/api/v1/jobs/${jobId}`)
}
