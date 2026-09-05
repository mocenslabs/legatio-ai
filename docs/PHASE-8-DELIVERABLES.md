# Phase 8: Agents & Automation - Deliverables

## Status: COMPLETE ✅

## Summary
Phase 8 introduces automated agents that can act within the governance system, along with automation rules that define when and how they act. Agents can create proposals, add comments, and send notifications based on trigger events and configurable conditions. The condition evaluation reuses the Policy Engine's existing evaluator for consistency and DRY principles.

## Deliverables

### 1. Models

#### Agent (`apps/agents/models/agent.py`)
- UUID primary key
- Name and description
- Agent type enum: AUTO_PROPOSER, AUTO_APPROVER, MONITOR, CUSTOM
- JSON config for type-specific settings
- Active status flag
- Creator reference
- Timestamps (created_at, updated_at)
- Property: `can_execute`

#### AutomationRule (`apps/agents/models/automation_rule.py`)
- UUID primary key
- Foreign key to Agent (cascade delete, related_name="rules")
- Name
- Trigger type enum: ON_PROPOSAL_CREATED, ON_PROPOSAL_SUBMITTED, ON_PROPOSAL_STATUS_CHANGED, ON_SCHEDULE, MANUAL
- JSON condition (evaluated against event context)
- Action type enum: CREATE_PROPOSAL, APPROVE_PROPOSAL, REJECT_PROPOSAL, ADD_COMMENT, NOTIFY, CUSTOM
- JSON action config
- Priority for rule evaluation order (lower runs first)
- Active status flag
- Creator reference
- Timestamps (created_at, updated_at)
- Properties: `can_fire`, `has_condition`

### 2. Service Layers

#### AgentService (`apps/agents/services/agent_service.py`)
- `create_agent()`: Creates an agent with type validation and audit logging
- `activate_agent()`: Activates an agent (idempotent)
- `deactivate_agent()`: Deactivates an agent (idempotent)
- `_get_agent()`: Shared retrieval helper

#### AutomationService (`apps/agents/services/automation_service.py`)
- `create_rule()`: Creates a rule with type validation and audit logging
- `process_trigger()`: Finds and executes all matching active rules for a trigger
- `execute_rule()`: Executes a specific rule against a context (for manual execution)
- `_evaluate_rule_condition()`: Evaluates conditions using the Policy Engine's `safe_evaluate`
- `_execute_rule_action()`: Dispatches to the appropriate action handler
- `_execute_notify()`: Sends a notification
- `_execute_add_comment()`: Adds a comment to an entity
- `_execute_create_proposal()`: Creates a proposal

### 3. Audit Integration

All agent and automation events are recorded:

| Action | Audit Log |
|--------|-----------|
| create_agent | AGENT_CREATED |
| activate_agent | AGENT_ACTIVATED |
| deactivate_agent | AGENT_DEACTIVATED |
| create_rule | AUTOMATION_RULE_CREATED |
| process_trigger / execute_rule | AUTOMATION_RULE_EXECUTED |

### 4. API Endpoints

#### Agent API (`/api/agents/`)
- `GET /api/agents/` - List agents (paginated, filterable)
- `POST /api/agents/` - Create agent (via service layer)
- `GET /api/agents/{id}/` - Retrieve with nested rules
- `PUT/PATCH /api/agents/{id}/` - Update agent
- `DELETE /api/agents/{id}/` - Delete agent
- `POST /api/agents/{id}/activate/` - Activate an agent
- `POST /api/agents/{id}/deactivate/` - Deactivate an agent
- Filters: `agent_type`, `is_active`

#### AutomationRule API (`/api/agents/rules/`)
- `GET /api/agents/rules/` - List rules (paginated, filterable)
- `POST /api/agents/rules/` - Create rule (via service layer)
- `GET /api/agents/rules/{id}/` - Retrieve a specific rule
- `PUT/PATCH /api/agents/rules/{id}/` - Update rule
- `DELETE /api/agents/rules/{id}/` - Delete rule
- `POST /api/agents/rules/{id}/execute/` - Execute rule manually against a context
- Filters: `agent`, `trigger_type`, `is_active`

### 5. Admin Interface (`apps/agents/admin.py`)

#### AgentAdmin
- Full CRUD for administrative management
- Inline of AutomationRule for managing rules within an agent
- Filtering by agent_type, is_active, created_at
- Search by name, description
- Optimized queryset with select_related

#### AutomationRuleAdmin
- Full CRUD for administrative management
- Filtering by trigger_type, action_type, is_active, created_at
- Search by name, agent name
- Optimized queryset with select_related

### 6. Test Coverage

#### Model Tests
- Agent creation, properties (can_execute), ordering
- AutomationRule creation, properties (can_fire, has_condition), cascade delete, priority ordering

#### Service Tests
- Agent creation with type validation
- Agent activation/deactivation (idempotent)
- Rule creation with validation
- Trigger processing with condition evaluation
- Fail-safe behavior (continues on rule failure)
- Manual rule execution

#### API Tests
- CRUD operations for agents and rules
- Lifecycle actions (activate, deactivate)
- Manual rule execution
- Filtering and pagination
- Authentication requirements (401)

**Coverage:** 90%+ across the agents app

### 7. Key Features

✅ **Automated Agents**: Configurable actors for governance automation
✅ **Agent Types**: AUTO_PROPOSER, AUTO_APPROVER, MONITOR, CUSTOM
✅ **Automation Rules**: Trigger-based rules with conditions and actions
✅ **Condition Evaluation**: Reuses Policy Engine's safe_evaluate (DRY)
✅ **Priority Ordering**: Rules evaluated by priority (lower first)
✅ **Fail-Safe Processing**: One rule's failure doesn't block others
✅ **Manual Execution**: Test rules against custom contexts via API
✅ **Audit Integration**: All agent events recorded
✅ **REST API**: Full lifecycle management via HTTP endpoints

## API Usage Examples

### Create an Agent
```bash
POST /api/agents/
{
  "name": "Proposal Bot",
  "description": "Automatically creates follow-up proposals",
  "agent_type": "AUTO_PROPOSER",
  "config": {"max_per_day": 10}
}
```

### Create an Automation Rule
```bash
POST /api/agents/rules/
{
  "agent": "uuid-of-agent",
  "name": "Comment on new proposals",
  "trigger_type": "ON_PROPOSAL_CREATED",
  "condition": {"field": "status", "operator": "==", "value": "DRAFT"},
  "action_type": "ADD_COMMENT",
  "action_config": {"content": "Thanks for submitting this proposal!"},
  "priority": 10
}
```

### Execute a Rule Manually
```bash
POST /api/agents/rules/{id}/execute/
{
  "context": {"status": "DRAFT", "proposal_id": "uuid"}
}

Response:
{
  "executed": true,
  "rule_id": "uuid"
}
```

#### Technical Notes

  - Condition evaluation delegates to the Policy Engine's safe_evaluate for consistency
  - Action handlers use local imports to avoid circular dependencies
  - Fail-safe processing ensures one rule's failure doesn't block others
  - Agent and rule creation routes through the service layer for audit logging
  - Type hints throughout (mypy strict compliant)
  - Google-style docstrings on all functions and classes

#### Next Steps (Phase 9)

  - Implement scheduled task execution with Celery (ON_SCHEDULE trigger)
  - Add webhook endpoints for external trigger sources
  - Implement APPROVE_PROPOSAL and REJECT_PROPOSAL actions
  - Add agent execution history and metrics
  - Build rate limiting for agent actions
  - Add agent permission scoping
  - Build frontend for agent management

#### Performance Considerations

  - Optimized queries with select_related on foreign keys
  - Indexes on frequently filtered fields (agent_type, is_active, trigger_type)
  - Rules ordered by priority for deterministic evaluation
  - Paginated list endpoints for large datasets
