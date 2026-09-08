# Phase 11: Webhooks & External Integrations - Deliverables

## Status: COMPLETE ✅

## Summary
Phase 11 introduces a robust webhook system that allows external systems to subscribe to specific events within the Legatio platform. When a subscribed event occurs (e.g., proposal created, agreement activated), the system asynchronously sends an HTTP POST request to the configured URL, secured with an HMAC-SHA256 signature.

## Deliverables

### 1. Models
- **`WebhookSubscription`**: Stores the target URL, a securely generated secret, a list of subscribed event types (using PostgreSQL `ArrayField`), and active status.

### 2. Service Layer
- **`WebhookService.trigger_event()`**: Finds all active subscriptions listening to a specific event type and dispatches them to a Celery task.

### 3. Celery Tasks
- **`deliver_webhook_task`**: Asynchronously sends the HTTP POST request. Includes:
  - HMAC-SHA256 signature generation (`X-Legatio-Signature` header).
  - Automatic retries (up to 3 times with a 60-second delay) on network failures or 5xx responses.
  - Graceful handling of deleted or deactivated subscriptions.

### 4. API Endpoints (`/api/webhooks/subscriptions/`)
- `GET /api/webhooks/subscriptions/` - List subscriptions (paginated, filterable by `is_active`).
- `POST /api/webhooks/subscriptions/` - Create a new subscription (auto-generates secret).
- `GET /api/webhooks/subscriptions/{id}/` - Retrieve a specific subscription.
- `PUT/PATCH /api/webhooks/subscriptions/{id}/` - Update a subscription.
- `DELETE /api/webhooks/subscriptions/{id}/` - Delete a subscription.

### 5. Admin Interface
- Full CRUD management for webhook subscriptions.
- Custom display column showing the number of subscribed events.
- Read-only display of the secret key for security reference.

### 6. System Integration
Webhooks are automatically triggered from existing service layers:
- **Proposals**: `PROPOSAL_CREATED`, `PROPOSAL_STATUS_CHANGED`
- **Agreements**: `AGREEMENT_ACTIVATED`, `AGREEMENT_TERMINATED`
- **Negotiations**: `NEGOTIATION_STARTED`, `NEGOTIATION_AGREED`, `NEGOTIATION_FAILED`

### 7. Test Coverage
- **Model Tests**: Creation, auto-generated secrets, active events filtering.
- **Service Tests**: Dispatching to matching subscriptions, skipping inactive/non-matching ones.
- **Task Tests**: HMAC signature correctness, successful delivery, retry logic on failure.
- **API Tests**: CRUD operations, filtering, authentication requirements.

## Security Considerations
- **HMAC-SHA256**: Payloads are serialized with `sort_keys=True` to ensure deterministic signing. The signature is sent in the `X-Legatio-Signature` header.
- **Secret Management**: Secrets are auto-generated using `secrets.token_hex(32)` and are read-only in the API to prevent accidental exposure or modification.
- **Fail-Safe**: If a webhook endpoint is down, the Celery task retries automatically without blocking the main application transaction.

## Next Steps (Phase 12)
- Deployment & CI/CD pipeline setup (Docker, GitHub Actions).
- API Rate Limiting refinement and advanced RBAC.
- Webhook delivery history and retry dashboard in the UI.
- Support for custom header injection in webhook subscriptions.
