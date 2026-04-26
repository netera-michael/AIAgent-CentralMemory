import axios from "axios"

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"
const API_KEY = import.meta.env.VITE_API_KEY || ""

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
  },
})

export interface Memory {
  id: string
  type: string
  title: string | null
  content: string
  summary: string | null
  scope: string
  sensitivity: string
  status: string
  confidence: number | null
  source_id: string | null
  entity_id: string | null
  canonical_group_id: string | null
  supersedes_memory_id: string | null
  valid_from: string | null
  valid_until: string | null
  created_at: string
  updated_at: string
  archived_at: string | null
  metadata_: Record<string, unknown> | null
}

export interface Entity {
  id: string
  type: string
  name: string
  normalized_name: string
  description: string | null
  created_at: string
  updated_at: string
  metadata_: Record<string, unknown> | null
}

export interface ReviewItem {
  id: string
  review_type: string
  status: string
  memory_id: string
  candidate_memory_id: string | null
  reason: string | null
  created_at: string
  resolved_at: string | null
}

export interface IngestionJob {
  id: string
  memory_id: string | null
  job_type: string
  status: string
  attempt_count: number
  last_error: string | null
  payload: Record<string, unknown> | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface APIKey {
  id: string
  name: string
  allowed_scopes: string[]
  can_read: boolean
  can_write: boolean
  active: boolean
  last_used_at: string | null
  created_at: string
}

export interface Stats {
  total: number
  by_status: Record<string, number>
  by_scope: Record<string, number>
  by_type: Record<string, number>
  total_entities: number
  pending_reviews: number
  pending_jobs: number
}

export interface SearchResult {
  memories: Memory[]
}

export const healthCheck = () => api.get("/health").then((r) => r.data)

export const getStats = () => api.get<Stats>("/stats").then((r) => r.data)

export const getMemories = (params: {
  skip?: number
  limit?: number
  include_scratch?: boolean
}) => api.get<Memory[]>("/memories", { params }).then((r) => r.data)

export const getMemory = (id: string) =>
  api.get<Memory>(`/memories/${id}`).then((r) => r.data)

export const createMemory = (data: Partial<Memory>) =>
  api.post<Memory>("/memories", data).then((r) => r.data)

export const updateMemory = (id: string, data: Partial<Memory>) =>
  api.patch<Memory>(`/memories/${id}`, data).then((r) => r.data)

export const archiveMemory = (id: string) =>
  api.post<Memory>(`/memories/${id}/archive`).then((r) => r.data)

export const purgeMemory = (id: string) =>
  api.delete(`/memories/${id}/purge`).then((r) => r.data)

export const semanticSearch = (data: {
  query: string
  scopes?: string[]
  type?: string
  entity_id?: string
  include_scratch?: boolean
  include_invalidated?: boolean
  limit?: number
  threshold?: number
}) => api.post<Memory[]>("/search/semantic", data).then((r) => r.data)

export const getEntities = (params?: { skip?: number; limit?: number }) =>
  api.get<Entity[]>("/entities", { params }).then((r) => r.data)

export const createEntity = (data: {
  name: string
  type: string
  description?: string
}) => api.post<Entity>("/entities", data).then((r) => r.data)

export const getReviewItems = (params?: { status?: string; limit?: number }) =>
  api.get<ReviewItem[]>("/review-items", { params }).then((r) => r.data)

export const resolveReviewItem = (
  id: string,
  action: string,
  notes?: string
) =>
  api
    .post<ReviewItem>(`/review-items/${id}/resolve`, {
      action,
      resolution_notes: notes,
    })
    .then((r) => r.data)

export const getIngestionJobs = (params?: {
  skip?: number
  limit?: number
  status?: string
}) => api.get<IngestionJob[]>("/ingestion-jobs", { params }).then((r) => r.data)

export const retryJob = (id: string) =>
  api.post<IngestionJob>(`/ingestion-jobs/${id}/retry`).then((r) => r.data)

export const getAPIKeys = () =>
  api.get<APIKey[]>("/api-keys").then((r) => r.data)

export const createAPIKey = (data: {
  name: string
  allowed_scopes: string[]
  can_read: boolean
  can_write: boolean
}) => api.post("/api-keys", data).then((r) => r.data)

export const revokeAPIKey = (id: string) =>
  api.post<APIKey>(`/api-keys/${id}/revoke`).then((r) => r.data)

export const getAuditLogs = (params?: {
  skip?: number
  limit?: number
}) => api.get("/audit-logs", { params }).then((r) => r.data)

export const reindex = (params?: {
  status?: string
  scope?: string
  force?: boolean
}) =>
  api
    .post("/reindex", null, { params })
    .then((r) => r.data)

export default api