import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { policyEvaluationApi, policyRulesApi } from '@/api/policies'
import type {
  PolicyEvaluationRequest,
  PolicyRuleCreatePayload,
  PolicyRuleListParams,
  PolicyRuleUpdatePayload,
} from '@/types/api/constitutions'
import { unwrapPaginated } from '@/utils/api'

/** Query-key factory for policy rules. */
export const policyRuleKeys = {
  all: ['policy-rules'] as const,
  lists: () => [...policyRuleKeys.all, 'list'] as const,
  list: (params: PolicyRuleListParams) => [...policyRuleKeys.lists(), params] as const,
  details: () => [...policyRuleKeys.all, 'detail'] as const,
  detail: (id: string) => [...policyRuleKeys.details(), id] as const,
}

export function usePolicyRules(params: PolicyRuleListParams = {}) {
  return useQuery({
    queryKey: policyRuleKeys.list(params),
    queryFn: async () => {
      const { data } = await policyRulesApi.list(params)
      return unwrapPaginated(data)
    },
  })
}

export function useCreatePolicyRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: PolicyRuleCreatePayload) => policyRulesApi.create(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: policyRuleKeys.lists() })
    },
  })
}

export function useUpdatePolicyRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: PolicyRuleUpdatePayload }) =>
      policyRulesApi.update(id, payload),
    onSuccess: (response) => {
      void queryClient.invalidateQueries({ queryKey: policyRuleKeys.lists() })
      queryClient.setQueryData(policyRuleKeys.detail(response.data.id), response.data)
    },
  })
}

export function useDeletePolicyRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => policyRulesApi.remove(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: policyRuleKeys.all })
    },
  })
}

/** Mutation wrapper for POST /policies/evaluate/ (rule testing UI). */
export function useEvaluatePolicy() {
  return useMutation({
    mutationFn: async (payload: PolicyEvaluationRequest) => {
      const { data } = await policyEvaluationApi.evaluate(payload)
      return data
    },
  })
}
