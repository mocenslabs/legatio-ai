import { apiClient } from '@/api/client'
import type {
  ConstitutionCreatePayload,
  ConstitutionListParams,
  ConstitutionUpdatePayload,
  PaginatedResponse,
} from '@/types/api/constitutions'
import type { Constitution } from '@/types/models/constitution'

type ConstitutionListResponse = PaginatedResponse<Constitution> | Constitution[]

export const constitutionsApi = {
  // CORREGIDO: Backend usa /api/constitutions/ NO /api/v1/constitutions/
  list(params?: ConstitutionListParams) {
    return apiClient.get<ConstitutionListResponse>('/constitutions/', { params })
  },
  get(id: string) {
    return apiClient.get<Constitution>(`/constitutions/${id}/`)
  },
  create(payload: ConstitutionCreatePayload) {
    return apiClient.post<Constitution>('/constitutions/', payload)
  },
  update(id: string, payload: ConstitutionUpdatePayload) {
    return apiClient.patch<Constitution>(`/constitutions/${id}/`, payload)
  },
  remove(id: string) {
    return apiClient.delete<void>(`/constitutions/${id}/`)
  },
  activate(id: string) {
    return apiClient.patch<Constitution>(`/constitutions/${id}/`, { is_active: true })
  },
}
