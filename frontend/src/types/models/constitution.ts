/**
 * Domain models for Constitutions and Policy Rules.
 *
 * Mirrors backend serializers:
 * - apps/constitutions/serializers/constitution.py
 * - apps/policies/serializers/policy_rule.py
 */

/** UUID v4 serialized as string. */
export type Uuid = string

/** ISO-8601 datetime string returned by DRF. */
export type IsoDateTime = string

/** Actions a PolicyRule enforces when its condition matches. */
export type RuleActionType = 'ALLOW' | 'DENY' | 'REQUIRE_APPROVAL'

/** Outcome returned by the Policy Engine evaluation endpoint. */
export type PolicyDecisionOutcome = 'ALLOW' | 'DENY' | 'REQUIRE_HUMAN_APPROVAL' | 'ERROR'

/** Risk levels assessed by the Policy Engine. */
export type PolicyRiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

/** Operators supported by rule conditions (backend-validated list). */
export type ConditionOperator =
  | '=='
  | '!='
  | '>'
  | '<'
  | '>='
  | '<='
  | 'in'
  | 'not_in'
  | 'contains'
  | 'exists'

/**
 * JSON condition attached to a PolicyRule.
 * `value` is optional only when operator === 'exists'.
 */
export interface RuleCondition {
  field: string
  operator: ConditionOperator
  value?: unknown
}

/** User-defined set of rules ("Constitution"). */
export interface Constitution {
  id: Uuid
  name: string
  description: string
  is_active: boolean
  created_at: IsoDateTime
  updated_at: IsoDateTime
}

/** Individual rule within a Constitution. */
export interface PolicyRule {
  id: Uuid
  name: string
  description: string
  condition: RuleCondition
  action_type: RuleActionType
  risk_level: PolicyRiskLevel
  requires_approval_from: string[]
  priority: number
  is_active: boolean
  /** UUID of the Constitution this rule belongs to. */
  constitution: Uuid
  created_at: IsoDateTime
  updated_at: IsoDateTime
}
