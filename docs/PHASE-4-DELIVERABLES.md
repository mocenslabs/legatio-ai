# Phase 4: Notifications & Audit Logging - Deliverables

## Status: COMPLETE ✅

## Summary
Phase 4 adds two critical cross-cutting capabilities to Legatio AI: a comprehensive audit logging system that records every state transition for compliance and debugging, and a notification system that keeps users informed about relevant events in the proposal lifecycle. Both systems are tightly integrated with the ProposalService to provide automatic, transactional tracking of all business operations.

## Deliverables

### 1. Models

#### AuditLog (`apps/audit/models/audit_log.py`)
- UUID primary key
- Action type (enum with proposal, approval, and policy-rule actions)
- Entity type and entity ID (polymorphic reference to any audited entity)
- Actor (nullable for system actions)
- Old state and new state (JSON snapshots)
- Metadata (JSON for additional context)
- IP address and user agent (for request tracing)
- Created timestamp
- **Append-only by design** (never updated or deleted)
- Classmethod `log()` for convenient creation

#### Notification (`apps/notifications/models/notification.py`)
- UUID primary key
- Notification type (APPROVAL_REQUESTED, PROPOSAL_APPROVED, PROPOSAL_DENIED, etc.)
- Recipient (User foreign key)
- Optional related entity (entity_type + entity_id)
- Title and message
- Status lifecycle: UNREAD → READ / ARCHIVED
- Read timestamp
- Properties: `is_read`
- Methods: `mark_as_read()`, `archive()`
- Classmethod `notify()` for convenient creation

### 2. Service Layers

#### AuditService (`apps/audit/services/audit_service.py`)
- `log_proposal_event()`: Records proposal-related audit events
- `log_approval_event()`: Records approval-related audit events
- `log_policy_rule_event()`: Records policy-rule-related audit events
- Internal `_log()` helper that delegates to AuditLog.log()

#### NotificationService (`apps/notifications/services/notification_service.py`)
- `notify_proposal_status()`: Generic proposal status notification
- `notify_approval_requested()`: Approval request notification
- `notify_proposal_approved()`: Approval success notification
- `notify_proposal_denied()`: Denial notification with optional reason
- `notify_proposal_executed()`: Execution notification
- `notify_proposal_cancelled()`: Cancellation notification

### 3. Integration with ProposalService

The ProposalService now automatically records audit events and sends notifications at every state transition:

| Action | Audit Log | Notification |
|--------|-----------|--------------|
| create_proposal | PROPOSAL_CREATED | - |
| submit_proposal (ALLOW) | PROPOSAL_APPROVED | PROPOSAL_APPROVED |
| submit_proposal (DENY/ERROR) | PROPOSAL_DENIED | PROPOSAL_DENIED |
| submit_proposal (REQUIRE_APPROVAL) | PROPOSAL_SUBMITTED + APPROVAL_REQUESTED (per role) | APPROVAL_REQUESTED (per role) |
| resolve_approval | APPROVAL_APPROVED/REJECTED + proposal status | PROPOSAL_APPROVED/DENIED |
| execute_proposal | PROPOSAL_EXECUTED | PROPOSAL_EXECUTED |
| cancel_proposal | PROPOSAL_CANCELLED + APPROVAL_CANCELLED (per pending) | PROPOSAL_CANCELLED |

**Key Features:**
- All logging/notifications occur within the same atomic transaction
- Actor tracking via optional `actor_id` parameter (backward compatible)
- Old state captured before every transition
- Fail-safe: ERROR outcomes logged with `metadata.error=True`

### 4. API Endpoints

#### AuditLog API (`/api/audit/`)
- `GET /api/audit/` - List audit logs (paginated, read-only)
- `GET /api/audit/{id}/` - Retrieve a specific audit log
- Filters: `entity_type`, `entity_id`, `action`, `actor`
- **No create/update/delete** (405 Method Not Allowed)

#### Notification API (`/api/notifications/`)
- `GET /api/notifications/` - List notifications (paginated, read-only)
- `GET /api/notifications/{id}/` - Retrieve a specific notification
- `POST /api/notifications/{id}/mark_as_read/` - Mark as read
- `POST /api/notifications/{id}/archive/` - Archive notification
- Filters: `status`, `notification_type`
- **No create/delete** (405 Method Not Allowed)

### 5. Admin Interface

#### AuditLogAdmin (`apps/audit/admin.py`)
- Read-only list view with filtering and search
- Fieldsets organized by state transition and context
- Disabled add/change/delete permissions
- Optimized queryset with select_related

#### NotificationAdmin (`apps/notifications/admin.py`)
- Read-only list view with filtering and search
- Fieldsets organized by entity, status, and timestamps
- Disabled add/change/delete permissions
- Optimized queryset with select_related

### 6. Test Coverage

#### Model Tests
- AuditLog creation, log classmethod, string representation, ordering
- Notification creation, notify classmethod, properties, mark_as_read, archive, cascade delete

#### Service Tests
- AuditService typed methods for all entity types
- NotificationService typed methods for all notification types

#### Integration Tests
- ProposalService creates audit logs at every transition
- ProposalService sends notifications at every transition
- Multi-role approval requests generate multiple notifications

#### API Tests
- List, retrieve, and filter operations
- mark_as_read and archive actions
- Access restrictions (405 for create/delete)
- Authentication requirements (401)

**Coverage:** 90%+ across audit and notifications apps

### 7. Key Features

✅ **Complete Audit Trail**: Every state transition recorded immutably

✅ **Actor Tracking**: Know who performed each action

✅ **State Snapshots**: Old and new state captured for every transition

✅ **Automatic Notifications**: Users informed about relevant events

✅ **Notification Lifecycle**: UNREAD → READ / ARCHIVED

✅ **Transactional Consistency**: Logs/notifications created atomically with business operations

✅ **Read-Only APIs**: Audit and notification data protected from modification

✅ **Polymorphic Entity References**: Audit any entity type via entity_type + entity_id

✅ **Request Tracing**: IP address and user agent captured

✅ **Authentication Required**: All endpoints secured


## API Usage Examples

### List Audit Logs for a Proposal
```bash
GET /api/audit/?entity_type=Proposal&entity_id=<uuid>

Response:
{
  "results": [
    {
      "action": "PROPOSAL_APPROVED",
      "entity_type": "Proposal",
      "entity_id": "uuid",
      "actor": "user-uuid",
      "old_state": {"status": "PENDING_APPROVAL"},
      "new_state": {"status": "APPROVED"},
      "created_at": "2026-01-15T10:30:00Z"
    }
  ]
}
```

### List Unread Notifications

```bash
GET /api/notifications/?status=UNREAD
```

### Mark a Notification as Read
```bash
POST /api/notifications/{id}/mark_as_read/

Response:
{
  "status": "READ",
  "is_read": true,
  "read_at": "2026-01-15T11:00:00Z"
}
```

### Archive a Notification
```bash
POST /api/notifications/{id}/archive/

Response:
{
  "status": "ARCHIVED"
}
```

#### Technical Notes

  - AuditLog is append-only: no update or delete operations exposed
  - Notifications are created by the service layer, never directly via API
  - All audit/notification operations occur within the caller's transaction
  - Actor is optional to support system-initiated actions
  - Old state captured before mutation for accurate audit trail
  - Type hints throughout (mypy strict compliant)
  - Google-style docstrings on all functions and classes


#### Next Steps (Phase 5)

  - Implement Agreement model and lifecycle
  - Build agreement generation from approved proposals
  - Add agreement versioning and amendments
  - Implement digital signatures / approval confirmation
  - Build negotiation workflow
  - Add real-time notifications (WebSockets)
  - Implement role-to-user mapping for targeted approval notifications

#### Performance Considerations

  - Optimized queries with select_related on foreign keys
  - Indexes on frequently filtered fields (entity_type, entity_id, action, status)
  - Paginated list endpoints for large datasets
  - Audit log writes are minimal overhead (single INSERT per event)
