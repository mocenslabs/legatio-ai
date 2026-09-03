# Phase 3: Proposals & Approvals Workflow - Deliverables

## Status: COMPLETE ✅

## Summary
Phase 3 implements the complete proposal lifecycle, from creation through policy evaluation, human approval (when required), and final execution. This phase bridges the Policy Engine (Phases 1 & 2) with real-world business operations, enabling users to propose actions that are automatically evaluated and routed through the appropriate approval workflow.

## Deliverables

### 1. Models

#### Proposal (`apps/proposals/models/proposal.py`)
- UUID primary key
- Title and description
- Action type, target resource, and JSON payload
- Status lifecycle: DRAFT → SUBMITTED → PENDING_APPROVAL/APPROVED/DENIED → EXECUTED/CANCELLED
- Policy decision snapshot (JSON)
- Foreign key to creator (User) and optional Constitution
- Timestamps (created_at, updated_at)
- Properties: `requires_approval`, `can_be_executed`

#### ApprovalRequest (`apps/approvals/models/approval_request.py`)
- UUID primary key
- Foreign key to Proposal (cascade delete)
- Required role (e.g., "manager", "director")
- Optional assigned user
- Status: PENDING, APPROVED, REJECTED, CANCELLED
- Decision tracking (decided_by, decided_at, notes)
- Properties: `is_pending`, `is_resolved`

### 2. Service Layer (`apps/proposals/services/proposal_service.py`)

#### ProposalService
- `create_proposal()`: Creates a proposal in DRAFT status
- `submit_proposal()`: Evaluates against policy engine and routes:
  - ALLOW → APPROVED
  - DENY → DENIED
  - ERROR → DENIED (fail-safe)
  - REQUIRE_HUMAN_APPROVAL → PENDING_APPROVAL + creates ApprovalRequests
- `resolve_approval()`: Resolves an individual approval request
- `execute_proposal()`: Marks an approved proposal as EXECUTED
- `cancel_proposal()`: Cancels a proposal and its pending approvals

**Key Features:**
- Atomic transactions for consistency
- `select_for_update()` to prevent race conditions
- Fail-safe: ERROR outcomes treated as DENY
- Any rejection immediately denies the proposal
- All approvals must approve for the proposal to be approved

### 3. Serializers

#### Proposal Serializers (`apps/proposals/serializers/proposal.py`)
- `ProposalSerializer`: Standard representation for CRUD
- `ProposalDetailSerializer`: Includes nested approval requests and computed properties
- `ProposalCreateSerializer`: Validates creation input (action_type, target_resource)

#### Approval Serializers (`apps/approvals/serializers/approval_request.py`)
- `ApprovalRequestSerializer`: Read-only representation
- `ResolveApprovalSerializer`: Validates resolve input (approved, notes)

### 4. API Views

#### ProposalViewSet (`apps/proposals/views/proposal.py`)
- Full CRUD operations
- Custom actions:
  - `POST /api/proposals/{id}/submit/`: Submit for policy evaluation
  - `POST /api/proposals/{id}/execute/`: Execute approved proposal
  - `POST /api/proposals/{id}/cancel/`: Cancel proposal
- Filtering by status
- Returns detail serializer (with nested approvals) on retrieve/list

#### ApprovalRequestViewSet (`apps/approvals/views/approval_request.py`)
- Read-only (list/retrieve) - creation managed by service layer
- Custom action:
  - `POST /api/approvals/{id}/resolve/`: Approve or reject
- Filtering by status, proposal, required_role
- No create/update/delete via API (405 Method Not Allowed)

### 5. Admin Interface

#### ProposalAdmin (`apps/proposals/admin.py`)
- List display with key fields
- Filtering by status, action_type, created_at
- Search by title, description, action_type
- Read-only inline of ApprovalRequest instances
- Optimized queryset with select_related

#### ApprovalRequestAdmin (`apps/approvals/admin.py`)
- List display with decision tracking
- Filtering by status, required_role
- Read-only fields (managed by service layer)
- Disabled add/change permissions

### 6. Test Coverage

#### Model Tests
- Proposal creation, properties, status transitions
- ApprovalRequest creation, properties, cascade delete
- Multiple approvals per proposal

#### Service Tests
- Full proposal lifecycle (create, submit, resolve, execute, cancel)
- Policy engine integration (ALLOW, DENY, REQUIRE_APPROVAL)
- Approval resolution logic (all approve, any reject)
- Invalid transitions raise appropriate errors

#### API Tests
- CRUD operations for proposals
- Lifecycle actions (submit, execute, cancel)
- Filtering and pagination
- Approval resolution via API
- Access restrictions (no direct approval creation)
- Authentication requirements

**Coverage:** 90%+ across proposals and approvals apps

### 7. Key Features

✅ **Automated Policy Evaluation**: Proposals automatically evaluated against active rules

✅ **Approval Request Generation**: Automatically creates requests for each required role

✅ **Fail-Safe Design**: Any error or rejection results in DENY

✅ **Race Condition Prevention**: Uses `select_for_update()` for concurrent safety

✅ **Audit Trail**: Policy decision snapshot stored on proposal

✅ **Flexible Approval Logic**: Any rejection denies; all must approve

✅ **Clear Status Lifecycle**: Explicit state machine for proposals

✅ **REST API**: Full lifecycle management via HTTP endpoints

✅ **Admin Interface**: Visual management with nested approval visibility

✅ **Authentication Required**: All endpoints secured

## API Usage Examples

### Create a Proposal
```bash
POST /api/proposals/
{
  "title": "Purchase Equipment",
  "action_type": "CREATE_PROPOSAL",
  "target_resource": "equipment",
  "payload": {"amount": 15000, "category": "IT"}
}
```
### Submit Policy Evaluation
```bash
POST /api/proposals/{id}/submit/

Response (if approval required):
{
  "id": "uuid",
  "title": "Purchase Equipment",
  "status": "PENDING_APPROVAL",
  "policy_decision": {
    "outcome": "REQUIRE_HUMAN_APPROVAL",
    "risk_level": "HIGH",
    "requires_approval_from": ["manager", "director"]
  },
  "approval_requests": [
    {"required_role": "manager", "status": "PENDING"},
    {"required_role": "director", "status": "PENDING"}
  ]
}
```
### Resolve an Approval

```bash
POST /api/approvals/{id}/resolve/
{
  "approved": true,
  "notes": "Budget approved for Q1"
}
```
### Execute an Approved Proposal

```bash
POST /api/proposals/{id}/execute/

Response:
{
  "status": "EXECUTED",
  "policy_decision": {...}
}
```

#### Technical Notes

  - All state transitions are atomic (wrapped in transactions)
  - Policy decision is stored as JSON snapshot for audit purposes
  - Approval requests are read-only via API (created by service layer)
  - Cascade delete: deleting a proposal deletes all its approval requests
  - Cancelling a proposal also cancels pending approval requests
  - Type hints throughout (mypy strict compliant)
  - Google-style docstrings on all functions and classes

#### Next Steps (Phase 4)

  - Implement actual execution logic for different action types
  - Add notification system for approval requests
  - Build audit logging for all state transitions
  - Implement agreement generation (Phase 5)
  - Add proposal comments/discussion thread
  - Build frontend for proposal management and approval UI

#### Performance Considerations

  - Optimized queries with select_related on foreign keys
  - Indexes on frequently filtered fields (status, created_at)
  - Efficient approval resolution (early exit on first rejection)
  - Paginated list endpoints for large datasets
