import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// JWT Token Management
const TOKEN_KEY = 'ludwigone_admin_token'

export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY)
}

export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token)
}

export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
}

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      removeToken()
      window.location.href = '/admin/login'
    }
    return Promise.reject(error)
  }
)

export interface Category {
  id: string
  name: string
  description?: string
  color?: string
  display_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SystemConfig {
  key: string
  value: string
  value_type: string
  description?: string
  is_secret: boolean
  created_at: string
  updated_at: string
}

export interface PromptTemplate {
  id: string
  name: string
  purpose: string
  template: string
  model_name: string
  temperature: number
  max_tokens: number
  token_limit?: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Job {
  id: string
  type: string
  status: string
  total_files: number
  processed_files: number
  failed_files: number
  original_filename: string
  created_at: string
}

// Categories API
export const getCategories = async (includeInactive = false): Promise<Category[]> => {
  const response = await api.get<Category[]>('/api/v1/admin/categories', {
    params: { include_inactive: includeInactive },
  })
  return response.data
}

export const createCategory = async (data: Partial<Category>): Promise<Category> => {
  const response = await api.post<Category>('/api/v1/admin/categories', data)
  return response.data
}

export const updateCategory = async (id: string, data: Partial<Category>): Promise<Category> => {
  const response = await api.put<Category>(`/api/v1/admin/categories/${id}`, data)
  return response.data
}

export const deleteCategory = async (id: string): Promise<void> => {
  await api.delete(`/api/v1/admin/categories/${id}`)
}

// Config API
export const getConfig = async (includeSecrets = false): Promise<SystemConfig[]> => {
  const response = await api.get<SystemConfig[]>('/api/v1/admin/config', {
    params: { include_secrets: includeSecrets },
  })
  return response.data
}

export const updateConfig = async (key: string, value: string): Promise<SystemConfig> => {
  const response = await api.put<SystemConfig>(`/api/v1/admin/config/${key}`, { value })
  return response.data
}

// Jobs API (for overview)
export const getJobs = async (): Promise<{ jobs: Job[]; total: number }> => {
  const response = await api.get('/api/v1/jobs', {
    params: { skip: 0, limit: 100 },
  })
  return response.data
}

export const deleteJob = async (jobId: string): Promise<void> => {
  await api.delete(`/api/v1/jobs/${jobId}`)
}

// Prompts API
export const getPrompts = async (includeInactive = false): Promise<PromptTemplate[]> => {
  const response = await api.get<PromptTemplate[]>('/api/v1/admin/prompts', {
    params: { include_inactive: includeInactive },
  })
  return response.data
}

export const createPrompt = async (data: Partial<PromptTemplate>): Promise<PromptTemplate> => {
  const response = await api.post<PromptTemplate>('/api/v1/admin/prompts', data)
  return response.data
}

export const updatePrompt = async (id: string, data: Partial<PromptTemplate>): Promise<PromptTemplate> => {
  const response = await api.put<PromptTemplate>(`/api/v1/admin/prompts/${id}`, data)
  return response.data
}

export const deletePrompt = async (id: string): Promise<void> => {
  await api.delete(`/api/v1/admin/prompts/${id}`)
}

// Auth API
export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface User {
  id: string
  username: string
  email: string
  is_active: boolean
  is_admin: boolean
  must_change_password: boolean
  created_at: string
  last_login_at?: string
}

export const login = async (credentials: LoginRequest): Promise<TokenResponse> => {
  const response = await api.post<TokenResponse>('/api/v1/auth/login', credentials)
  if (response.data.access_token) {
    setToken(response.data.access_token)
  }
  return response.data
}

export const logout = (): void => {
  removeToken()
  window.location.href = '/admin/login'
}

export const getCurrentUser = async (): Promise<User> => {
  const response = await api.get<User>('/api/v1/auth/me')
  return response.data
}

export const isAuthenticated = (): boolean => {
  return getToken() !== null
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

export const changePassword = async (data: ChangePasswordRequest): Promise<{ message: string }> => {
  const response = await api.post('/api/v1/auth/change-password', data)
  return response.data
}
