# Phase 6: Negotiations & Discussions - Deliverables

## Status: COMPLETE ✅

## Summary
Phase 6 adds collaboration capabilities to Legatio AI through a generic comment/discussion system and a structured negotiation workflow. Comments use a polymorphic reference pattern to support discussion across proposals, agreements, and negotiations. Negotiations enable parties to exchange offers with automatic round numbering, culminating in agreement or failure. Both systems integrate fully with audit logging and notifications.

## Deliverables

### 1. Models

#### Comment (`apps/negotiations/models/comment.py`)
- UUID primary key
- Polymorphic entity reference (entity_type + entity_id)
- Entity type enum: Proposal, Agreement, Negotiation
- Author reference
- Content text
- Self-referential parent for threaded replies
- Timestamps (created_at, updated_at)
- Property: `is_reply`

#### Negotiation (`apps/negotiations/models/negotiation.py`)
- UUID primary key
- Foreign key to Proposal (cascade delete, related_name="negotiations")
- Title and description
- Status lifecycle: OPEN → IN_PROGRESS → AGREED / FAILED / CANCELLED
- Initiator reference
- Timestamps (created_at, updated_at)
- Properties: `is_active`, `is_concluded`

#### NegotiationOffer (`apps/negotiations/models/negotiation_offer.py`)
- UUID primary key
- Foreign key to Negotiation (cascade delete, related_name="offers")
- Offerer reference
- Structured JSON terms
- Status lifecycle: PENDING → ACCEPTED / REJECTED / WITHDRAWN
- Sequential round_number
- Optional notes
- Timestamps (created_at, updated_at)
- Properties: `is_pending`, `is_resolved`

### 2. Service Layers

#### CommentService (`apps/negotiations/services/comment_service.py`)
- `add_comment()`: Creates a comment with validation and audit logging
- `delete_comment()`: Deletes a comment (author-only enforcement)
- `_notify_comment()`: Notifies entity owners about new comments (Proposal support)

#### NegotiationService (`apps/negotiations/services/negotiation_service.py`)
- `create_negotiation()`: Creates a negotiation tied to a proposal
- `start_negotiation()`: Transitions OPEN → IN_PROGRESS
- `make_offer()`: Creates an offer with automatic round numbering
- `accept_offer()`: Accepts an offer and concludes negotiation as AGREED
- `reject_offer()`: Rejects a pending offer
- `withdraw_offer()`: Withdraws an offer (creator-only)
- `conclude_negotiation()`: Concludes as FAILED or CANCELLED
- `_get_negotiation()`: Shared retrieval helper
- `_resolve_offer_transition()`: Shared helper for ACCEPTED/REJECTED transitions

### 3. Audit & Notification Integration

All negotiation and comment events are recorded:

| Action | Audit Log | Notification |
|--------|-----------|--------------|
| add_comment | COMMENT_ADDED | COMMENT_ADDED (Proposal owner) |
| delete_comment | COMMENT_DELETED | - |
| create_negotiation | NEGOTIATION_CREATED | - |
| start_negotiation | NEGOTIATION_STARTED | NEGOTIATION_STARTED |
| make_offer | OFFER_CREATED | OFFER_RECEIVED |
| accept_offer | OFFER_ACCEPTED + NEGOTIATION_AGREED | OFFER_ACCEPTED |
| reject_offer | OFFER_REJECTED | OFFER_REJECTED |
| withdraw_offer | OFFER_WITHDRAWN | - |
| conclude_negotiation | NEGOTIATION_FAILED/CANCELLED | - |

### 4. API Endpoints

#### Comment API (`/api/negotiations/comments/`)
- `GET /api/negotiations/comments/` - List comments (paginated, filterable)
- `POST /api/negotiations/comments/` - Create comment (via service layer)
- `GET /api/negotiations/comments/{id}/` - Retrieve a comment
- `DELETE /api/negotiations/comments/{id}/` - Delete own comment
- Filters: `entity_type`, `entity_id`, `author`
- **No update** (405 Method Not Allowed)

#### Negotiation API (`/api/negotiations/`)
- `GET /api/negotiations/` - List negotiations (paginated, filterable)
- `POST /api/negotiations/` - Create negotiation (via service layer)
- `GET /api/negotiations/{id}/` - Retrieve with nested offers
- `POST /api/negotiations/{id}/start/` - Start an open negotiation
- `POST /api/negotiations/{id}/make_offer/` - Make an offer
- `POST /api/negotiations/{id}/conclude/` - Conclude as FAILED or CANCELLED
- Filters: `status`, `proposal`

#### NegotiationOffer API (`/api/negotiations/offers/`)
- `GET /api/negotiations/offers/` - List offers (paginated, read-only)
- `GET /api/negotiations/offers/{id}/` - Retrieve a specific offer
- `POST /api/negotiations/offers/{id}/accept/` - Accept an offer
- `POST /api/negotiations/offers/{id}/reject/` - Reject an offer
- `POST /api/negotiations/offers/{id}/withdraw/` - Withdraw an offer
- Filters: `negotiation`, `status`, `offered_by`
- **No create** (405 Method Not Allowed) - offers created via negotiation make_offer

### 5. Admin Interface (`apps/negotiations/admin.py`)

#### CommentAdmin
- Read-only with deletion allowed for moderation
- List display with truncated content
- Filtering by entity_type, created_at
- Search by content, author email
- Optimized queryset with select_related

#### NegotiationAdmin
- Read-only (lifecycle managed by service layer)
- Inline of NegotiationOffer (read-only)
- Filtering by status, created_at
- Search by title, description, proposal title
- Optimized queryset with select_related

#### NegotiationOfferAdmin
- Read-only (managed by service layer)
- Filtering by status, created_at
- Search by negotiation title, notes
- Optimized queryset with select_related

### 6. Test Coverage

#### Model Tests
- Comment creation, replies, is_reply property
- Negotiation creation, is_active/is_concluded properties
- NegotiationOffer creation, is_pending/is_resolved properties
- Cascade delete relationships

#### Service Tests
- Comment creation, replies, author-only deletion
- Invalid entity_type handling
- Negotiation creation and start transitions
- Offer creation with sequential round numbers
- Accept/reject/withdraw offer logic
- Creator-only withdrawal enforcement
- Conclude negotiation transitions

#### API Tests
- CRUD operations for comments and negotiations
- Lifecycle actions (start, make_offer, conclude)
- Offer actions (accept, reject, withdraw)
- Filtering and pagination
- Access restrictions (405 for update/create)
- Author-only deletion enforcement
- Authentication requirements (401)

**Coverage:** 90%+ across the negotiations app

### 7. Key Features

✅ **Generic Comments**: Polymorphic pattern supports proposals, agreements, negotiations

✅ **Threaded Discussions**: Self-referential parent enables nested replies

✅ **Author-Only Deletion**: Comments can only be deleted by their author

✅ **Structured Negotiations**: Clear lifecycle from OPEN to conclusion

✅ **Automatic Round Numbering**: Offers get sequential round numbers

✅ **Offer Lifecycle**: PENDING → ACCEPTED/REJECTED/WITHDRAWN

✅ **Acceptance Concludes**: Accepting an offer automatically marks negotiation as AGREED

✅ **Creator-Only Withdrawal**: Only offer creators can withdraw their offers

✅ **Audit Integration**: All events recorded with actor and state snapshots

✅ **Notification Integration**: Users informed of relevant events

✅ **REST API**: Full lifecycle management via HTTP endpoints

## API Usage Examples

### Add a Comment to a Proposal
```bash
POST /api/negotiations/comments/
{
  "entity_type": "Proposal",
  "entity_id": "uuid-of-proposal",
  "content": "I have concerns about the timeline."
}
```

### Reply to a Comment
```bash
POST /api/negotiations/comments/
{
  "entity_type": "Proposal",
  "entity_id": "uuid-of-proposal",
  "content": "The timeline is negotiable.",
  "parent": "uuid-of-parent-comment"
}
```

### Create a Negotiation
```bash
POST /api/negotiations/
{
  "proposal": "uuid-of-proposal",
  "title": "Q1 Contract Negotiation",
  "description": "Negotiating terms for Q1 service agreement"
}
```

### Make an Offer
```bash
POST /api/negotiations/{id}/make_offer/
{
  "terms": {"price": 50000, "duration": "3 months"},
  "notes": "Initial offer with standard terms"
}

Response (201):
{
  "round_number": 1,
  "terms": {"price": 50000, "duration": "3 months"},
  "status": "PENDING"
}
```

### Accept an Offer
```bash
POST /api/negotiations/offers/{id}/accept/

Response:
{
  "status": "ACCEPTED"
}
# Negotiation automatically transitions to AGREED
```

#### Technical Notes

  - Comments use polymorphic references (entity_type + entity_id) for flexibility
  - Comment deletion is enforced at the service layer (author-only)
  - Negotiation offers are created exclusively through the make_offer action
  - Round numbers are calculated dynamically based on existing offers
  - Accepting an offer atomically concludes the negotiation as AGREED
  - Withdrawal is restricted to the offer creator
  - Type hints throughout (mypy strict compliant)
  - Google-style docstrings on all functions and classes


#### Next Steps (Phase 7)

  - Implement real-time notifications (WebSockets/Channels)
  - Build role-to-user mapping for targeted notifications
  - Add negotiation participant management
  - Implement offer counter-offer linking
  - Build scheduled tasks for agreement expiration
  - Add negotiation history timeline view
  - Build frontend for negotiation interface

#### Performance Considerations

  - Optimized queries with select_related on foreign keys
  - Indexes on frequently filtered fields (entity_type, entity_id, status)
  - Paginated list endpoints for large datasets
  - Offer queries indexed by (negotiation, status)
