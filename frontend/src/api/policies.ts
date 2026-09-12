import { apiClient } from '@/api/client'
import type {
  PaginatedResponse,
  PolicyEvaluationRequest,
  PolicyEvaluationResponse,
  PolicyRuleCreatePayload,
  PolicyRuleListParams,
  PolicyRuleUpdatePayload,
} from '@/types/api/constitutions'
import type { PolicyRule } from '@/types/models/constitution'

type PolicyRuleListResponse = PaginatedResponse<PolicyRule> | PolicyRule[]

export const policyRulesApi = {
  list(params?: PolicyRuleListParams) {
    return apiClient.get<PolicyRuleListResponse>('/policies/rules/', { params })
  },
  get(id: string) {
    return apiClient.get<PolicyRule>(`/policies/rules/${id}/`)
  },
  create(payload: PolicyRuleCreatePayload) {
    return apiClient.post<PolicyRule>('/policies/rules/', payload)
  },
  update(id: string, payload: PolicyRuleUpdatePayload) {
    return apiClient.patch<PolicyRule>(`/policies/rules/${id}/`, payload)
  },
  remove(id: string) {
    return apiClient.delete<void>(`/policies/rules/${id}/`)
  },
}

export const policyEvaluationApi = {
  evaluate(payload: PolicyEvaluationRequest) {
    return apiClient.post<PolicyEvaluationResponse>('/policies/evaluate/', payload)
  },
}
