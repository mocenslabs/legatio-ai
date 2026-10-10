export interface Agent {
  id: string
  name: string
  agent_type: string
  status?: string
  description?: string
  owner?: string | null
  created_at?: string
  updated_at?: string
}

export interface PolicyRule {
  id?: string
  rule_number: number
  name: string
  category: string
  field: string
  operator: string
  value: unknown
  action: string
  priority?: number
  description?: string
}

export interface Constitution {
  id: string
  name: string
  description?: string
  status: string
  agent?: string | Agent
  agent_id?: string
  active_version?: {
    id: string
    version_number: number
    status: string
    rules?: PolicyRule[]
  } | null
  created_at?: string
  updated_at?: string
}

export interface NegotiationRoom {
  id: string
  reference_code?: string
  title: string
  user_instruction?: string
  status: string
  current_round?: number
  max_rounds?: number
  user_agent_id?: string
  external_agent_id?: string
  constitution_id?: string
  created_at?: string
  updated_at?: string
}

export interface Proposal {
  id: string
  amount?: string | number | null
  currency?: string
  action_type?: string
  status?: string
  round_number?: number
  data_fields_requested?: string[]
  contract_length_months?: number | null
  auto_renewal?: boolean | null
  terms?: Record<string, unknown>
}

export interface ApprovalRequest {
  id: string
  status: string
  summary?: string
  expires_at?: string
  created_at?: string
  proposal?: Proposal
  room?: string | NegotiationRoom
  room_id?: string
  risk_level?: string
}

export interface CreateConstitutionPayload {
  name: string
  description?: string
  agent_id: string
  rules?: Array<Omit<PolicyRule, 'id'>>
}

export interface CreateNegotiationPayload {
  title: string
  user_instruction: string
  user_agent_id: string
  external_agent_id: string
  constitution_id: string
  max_rounds?: number
}

export interface Agreement {
  id: string
  reference_code?: string
  status: string
  room?: string
  room_reference_code?: string
  proposal?: string
  proposal_amount?: string | null
  proposal_action_type?: string
  constitution_version?: string
  constitution_version_number?: number
  canonical_json?: string | Record<string, unknown>
  canonical_hash?: string
  parties?: unknown
  terms_summary?: string | Record<string, unknown>
  signed_at?: string | null
  executed_at?: string | null
  is_signed?: boolean
  is_verified?: boolean
  created_at?: string
}

export interface AuditEvent {
  id: string
  event_type: string
  actor_type?: string
  actor_id?: string | null
  entity_type?: string
  entity_id?: string
  payload?: Record<string, unknown>
  created_at?: string
  sequence_number?: number
  event_hash?: string
}
