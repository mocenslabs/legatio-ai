import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { constitutionsApi } from '@/api/constitutions'
import type {
  ConstitutionCreatePayload,
  ConstitutionListParams,
  ConstitutionUpdatePayload,
} from '@/types/api/constitutions'
import { unwrapPaginated } from '@/utils/api'

/** Query-key factory (TanStack Query best practice). */
export const constitutionKeys = {
  all: ['constitutions'] as const,
  lists: () => [...constitutionKeys.all, 'list'] as const,
  list: (params: ConstitutionListParams) => [...constitutionKeys.lists(), params] as const,
  details: () => [...constitutionKeys.all, 'detail'] as const,
  detail: (id: string) => [...constitutionKeys.details(), id] as const,
}

export function useConstitutions(params: ConstitutionListParams = {}) {
  return useQuery({
    queryKey: constitutionKeys.list(params),
    queryFn: async () => {
      const { data } = await constitutionsApi.list(params)
      return unwrapPaginated(data)
    },
  })
}

export function useConstitution(id: string) {
  return useQuery({
    queryKey: constitutionKeys.detail(id),
    queryFn: async () => {
      const { data } = await constitutionsApi.get(id)
      return data
    },
    enabled: Boolean(id),
  })
}

export function useCreateConstitution() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: ConstitutionCreatePayload) => constitutionsApi.create(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: constitutionKeys.lists() })
    },
  })
}

export function useUpdateConstitution() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ConstitutionUpdatePayload }) =>
      constitutionsApi.update(id, payload),
    onSuccess: (response) => {
      void queryClient.invalidateQueries({ queryKey: constitutionKeys.lists() })
      queryClient.setQueryData(constitutionKeys.detail(response.data.id), response.data)
    },
  })
}

export function useDeleteConstitution() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => constitutionsApi.remove(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: constitutionKeys.all })
    },
  })
}

export function useActivateConstitution() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => constitutionsApi.activate(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: constitutionKeys.all })
    },
  })
}
