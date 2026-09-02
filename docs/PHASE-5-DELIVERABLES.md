# Phase 5: Agreements - Deliverables

## Status: COMPLETE ✅

## Summary
Phase 5 implements the Agreement model and lifecycle, representing the formal, binding outcome of approved and executed proposals. The phase introduces immutable versioning for full amendment tracking, automatic generation of agreements from executed proposals, and complete integration with the audit logging and notification systems established in Phase 4.

## Deliverables

### 1. Models

#### Agreement (`apps/agreements/models/agreement.py`)
- UUID primary key
- Title and description
- Optional link to originating Proposal (SET_NULL on delete)
- Optional link to Constitution (SET_NULL on delete)
- Status lifecycle: DRAFT → ACTIVE → SUSPENDED / COMPLETED / TERMINATED
- Structured JSON terms
- Effective date and optional expiration date
- Creator reference
- Timestamps (created_at, updated_at)
- Properties: `is_active`, `is_expired`, `can_be_activated`

#### AgreementVersion (`apps/agreements/models/agreement_version.py`)
- UUID primary key
- Foreign key to Agreement (cascade delete, related_name="versions")
- Sequential version_number with unique constraint per agreement
- Snapshot of title and terms at the time of the version
- Change reason describing why the version was created
- Creator reference
- Created timestamp
- **Immutable by design** (never updated after creation)

### 2. Service Layer (`apps/agreements/services/agreement_service.py`)

#### AgreementService
- `create_agreement()`: Creates a DRAFT agreement + initial version
- `generate_from_proposal()`: Generates an agreement from an EXECUTED proposal
- `activate_agreement()`: Activates a draft (sets effective_date if not set)
- `amend_agreement()`: Amends an active agreement, creating a new version
- `complete_agreement()`: Completes an active agreement
- `terminate_agreement()`: Terminates an active agreement with optional reason
- `_transition_to_final()`: Shared helper for COMPLETED/TERMINATED transitions
- `_create_version()`: Creates sequential version snapshots

**Key Features:**
- Atomic transactions for all state changes
- Automatic versioning on create and amend
- `select_for_update()` to prevent race conditions
- Preserves existing effective_date on activation
- Only EXECUTED proposals can generate agreements
- Only ACTIVE agreements can be amended or finalized

### 3. Audit & Notification Integration

All agreement lifecycle events are recorded and notified:

| Action | Audit Log | Notification |
|--------|-----------|--------------|
| create_agreement | AGREEMENT_CREATED | - |
| generate_from_proposal | AGREEMENT_CREATED | - |
| activate_agreement | AGREEMENT_ACTIVATED | AGREEMENT_ACTIVATED |
| amend_agreement | AGREEMENT_AMENDED | - |
| complete_agreement | AGREEMENT_COMPLETED | AGREEMENT_COMPLETED |
| terminate_agreement | AGREEMENT_TERMINATED | AGREEMENT_TERMINATED |

### 4. API Endpoints

#### Agreement API (`/api/agreements/`)
- `GET /api/agreements/` - List agreements (paginated, filterable)
- `POST /api/agreements/` - Create agreement (via service layer)
- `GET /api/agreements/{id}/` - Retrieve with nested versions
- `PUT/PATCH /api/agreements/{id}/` - Update agreement
- `DELETE /api/agreements/{id}/` - Delete agreement
- `POST /api/agreements/{id}/activate/` - Activate a draft
- `POST /api/agreements/{id}/amend/` - Amend (creates new version)
- `POST /api/agreements/{id}/complete/` - Complete an active agreement
- `POST /api/agreements/{id}/terminate/` - Terminate with optional reason
- `POST /api/agreements/generate_from_proposal/` - Generate from executed proposal
- Filters: `status`, `proposal`

#### AgreementVersion API (`/api/agreements/versions/`)
- `GET /api/agreements/versions/` - List versions (paginated, read-only)
- `GET /api/agreements/versions/{id}/` - Retrieve a specific version
- Filters: `agreement`
- **No create/update/delete** (405 Method Not Allowed)

### 5. Admin Interface (`apps/agreements/admin.py`)

#### AgreementAdmin
- Full CRUD for administrative management
- List display with key fields and relationships
- Filtering by status, created_at, effective_date
- Search by title, description
- Read-only inline of AgreementVersion history
- Optimized queryset with select_related

#### AgreementVersionAdmin
- Read-only list view (immutable snapshots)
- Filtering by created_at
- Search by title, change_reason, agreement title
- Disabled add/change/delete permissions
- Optimized queryset with select_related

### 6. Test Coverage

#### Model Tests
- Agreement creation, properties (is_active, is_expired, can_be_activated)
- AgreementVersion creation, unique constraint, cascade delete
- String representations and ordering

#### Service Tests
- Agreement creation with initial version
- Generation from executed proposals (and rejection of non-executed)
- Activation with effective_date handling
- Amendments creating new versions
- Complete and terminate transitions
- Invalid transition errors

#### API Tests
- CRUD operations for agreements
- Creation via service (initial version included in response)
- Lifecycle actions (activate, amend, complete, terminate)
- generate_from_proposal endpoint
- Version listing and filtering
- Access restrictions (405 for version creation)
- Authentication requirements (401)

**Coverage:** 90%+ across the agreements app

### 7. Key Features

✅ **Formal Agreement Model**: Binding outcomes of approved proposals
✅ **Immutable Versioning**: Full history of terms and amendments
✅ **Sequential Version Numbers**: Unique per agreement, auto-incremented
✅ **Generation from Proposals**: Seamless bridge from execution to agreement
✅ **Complete Lifecycle**: DRAFT → ACTIVE → COMPLETED/TERMINATED/SUSPENDED
✅ **Effective Date Handling**: Auto-set on activation, preserved if pre-set
✅ **Amendment Tracking**: Every change creates a version with reason
✅ **Audit Integration**: All events recorded with actor and state snapshots
✅ **Notification Integration**: Users informed of lifecycle changes
✅ **REST API**: Full lifecycle management via HTTP endpoints
✅ **Read-Only Versions**: Version history protected from modification

## API Usage Examples

### Create an Agreement Directly
```bash
POST /api/agreements/
{
  "title": "Service Agreement",
  "description": "Q1 service contract",
  "terms": {"duration": "3 months", "value": 50000}
}

Response (201):
{
  "id": "uuid",
  "title": "Service Agreement",
  "status": "DRAFT",
  "versions": [
    {"version_number": 1, "title": "Service Agreement", "terms": {...}}
  ],
  "is_active": false,
  "can_be_activated": true
}
```
### Generata from an Executed Proposal
```bash
POST /api/agreements/generate_from_proposal/
{
  "proposal_id": "uuid-of-executed-proposal"
}
```

### Activate an Agreement
```bash
POST /api/agreements/{id}/activate/

Response:
{
  "status": "ACTIVE",
  "effective_date": "2026-09-02T10:00:00Z",
  "is_active": true
}
```

### Amend an Agreement
```bash
POST /api/agreements/{id}/amend/
{
  "terms": {"duration": "6 months", "value": 95000},
  "change_reason": "Extended contract duration and value"
}

Response:
{
  "terms": {"duration": "6 months", "value": 95000},
  "versions": [
    {"version_number": 1, "terms": {...}},
    {"version_number": 2, "terms": {...}, "change_reason": "Extended contract duration and value"}
  ]
}
```

### Terminate an Agreement
```bash
POST /api/agreements/{id}/terminate/
{
  "reason": "Mutual agreement to end early"
}
```

#### Technical Notes

  - Agreement creation routes through the service layer to guarantee the initial version and audit log are created atomically
  - Versions are immutable snapshots; the unique constraint on (agreement, version_number) prevents duplicates
  - Only ACTIVE agreements can be amended, ensuring drafts and finalized agreements remain stable
  - The _transition_to_final helper unifies COMPLETED and TERMINATED logic
  - effective_date is preserved if already set during activation
  - Type hints throughout (mypy strict compliant)
  - Google-style docstrings on all functions and classes


#### Next Steps (Phase 6)

  - Implement real-time notifications (WebSockets/Channels)
  - Build role-to-user mapping for targeted approval notifications
  - Implement negotiation workflow between parties
  - Add agreement digital signatures / confirmation flow
  - Build proposal comments and discussion threads
  - Implement scheduled tasks for agreement expiration handling
  - Build frontend for agreement management and version history

#### Performance Considerations

  - Optimized queries with select_related on foreign keys
  - Indexes on frequently filtered fields (status, created_at, effective_date)
  - Paginated list endpoints for large datasets
  - Version lookups indexed by (agreement, version_number)
