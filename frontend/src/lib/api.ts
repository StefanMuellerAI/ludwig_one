import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
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
export const downloadArchive = (jobId: string) => {
  window.open(`${API_BASE_URL}/api/v1/jobs/${jobId}/download`, '_blank')
}

// Download insight XML
export const downloadInsight = (jobId: string) => {
  window.open(`${API_BASE_URL}/api/v1/jobs/${jobId}/insight`, '_blank')
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
