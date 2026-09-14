import type {
  PolicyDecisionOutcome,
  PolicyRiskLevel,
  RuleActionType,
  RuleCondition,
  Uuid,
} from '@/types/models/constitution'

/** DRF pagination envelope (used when DEFAULT_PAGINATION_CLASS is enabled). */
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/** Query params for GET /constitutions/. */
export interface ConstitutionListParams {
  is_active?: boolean
}

export interface ConstitutionCreatePayload {
  name: string
  description?: string
  is_active?: boolean
}

export type ConstitutionUpdatePayload = Partial<ConstitutionCreatePayload>

/** Query params for GET /policies/rules/. */
export interface PolicyRuleListParams {
  constitution?: Uuid
  is_active?: boolean
  action_type?: RuleActionType
  risk_level?: PolicyRiskLevel
}

export interface PolicyRuleCreatePayload {
  name: string
  description?: string
  condition: RuleCondition
  action_type: RuleActionType
  risk_level: PolicyRiskLevel
  requires_approval_from?: string[]
  priority?: number
  is_active?: boolean
  constitution: Uuid
}

export type PolicyRuleUpdatePayload = Partial<PolicyRuleCreatePayload>

/** POST /policies/evaluate/ request body. */
export interface PolicyEvaluationRequest {
  action_type: string
  target_resource: string
  payload: Record<string, unknown>
  actor_id: Uuid
  constitution_id?: Uuid | null
}

/** POST /policies/evaluate/ response body. */
export interface PolicyEvaluationResponse {
  outcome: PolicyDecisionOutcome
  risk_level: PolicyRiskLevel
  reason: string
  matched_rules: Uuid[]
  requires_approval_from: string[]
  timestamp: string
}
