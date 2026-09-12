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
  /**
   * Activate a constitution.
   *
   * NOTE: the backend exposes no dedicated /activate endpoint yet
   * (see 02-ARCHITECTURE.md §9.2 note); activation is performed via
   * PATCH is_active=true until the dedicated action lands.
   */
  activate(id: string) {
    return apiClient.patch<Constitution>(`/constitutions/${id}/`, { is_active: true })
  },
}
