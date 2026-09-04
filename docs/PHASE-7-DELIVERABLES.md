# Phase 7: Real-time Notifications (WebSockets) - Deliverables

## Status: COMPLETE ✅

## Summary
Phase 7 introduces real-time notification delivery over WebSockets using Django Channels. When a notification is created in the system, it can be pushed instantly to the recipient's connected WebSocket session. The implementation is fail-safe: if the channel layer is unavailable or the real-time push fails, the notification remains safely persisted in the database.

## Deliverables

### 1. ASGI Configuration

- `legatio/asgi.py` updated to support both HTTP and WebSocket protocols
- WebSocket routing enabled via `ProtocolTypeRouter`
- JWT authentication middleware applied to WebSocket connections
- Notification WebSocket endpoint mounted at `/ws/notifications/`

### 2. JWT WebSocket Authentication

- `core/websocket_auth.py`
- `JWTAuthMiddleware` extracts JWT from query string:
  - `ws://host/ws/notifications/?token=<access_token>`
- Token validated using SimpleJWT `AccessToken`
- Invalid or missing tokens result in `AnonymousUser`
- Consumer rejects unauthenticated connections

### 3. NotificationConsumer

- `apps/notifications/consumers.py`
- Async WebSocket consumer using `AsyncJsonWebsocketConsumer`
- Authenticated users are added to a personal group:
  - `notifications_{user_id}`
- Users leave their group on disconnect
- Handles `send_notification` events from the channel layer
- Sends JSON payloads to connected clients:

```json
{
  "type": "notification",
  "data": {
    "id": "uuid",
    "notification_type": "PROPOSAL_APPROVED",
    "title": "Proposal approved",
    "message": "Your proposal has been approved.",
    "status": "UNREAD"
  }
}
```

#### 4. Real-time Delivery Integration

  - apps/notifications/services/realtime.py
  - send_realtime_notification() sends messages to user groups
  - Fail-safe behavior:
     -  If channel layer is unavailable, logs warning and continues
     -  If group send fails, logs exception and continues
  - Notification persistence is never blocked by WebSocket delivery issues

#### 5. JSON-safe Serialization

  - Notifications are serialized using NotificationSerializer
  - Payload is rendered through DRF JSONRenderer before delivery
  - Ensures UUID, datetime, and other non-native types are JSON-safe

#### 6. Tests

  - Real-time helper tests:
     -  No exception when channel layer is unavailable
     -  No exception when group send fails
  - Consumer tests:
     -  Anonymous connections are rejected
     -  Authenticated connections are accepted
     -  Messages are delivered to the user's notification group
  - Tests use InMemoryChannelLayer to avoid Redis dependency

  ## API / WebSocket Usage

  ### Connect
```bash
const token = "ACCESS_TOKEN";
const socket = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${token}`);

socket.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  console.log(payload.type);
  console.log(payload.data);
};
```

### Expected Payload
```bash
{
  "type": "notification",
  "data": {
    "id": "uuid",
    "notification_type": "APPROVAL_REQUESTED",
    "recipient": "user-uuid",
    "entity_type": "Proposal",
    "entity_id": "proposal-uuid",
    "title": "Approval required",
    "message": "Approval is required for your proposal.",
    "status": "UNREAD",
    "is_read": false,
    "read_at": null,
    "created_at": "2026-09-04T13:30:00Z",
    "updated_at": "2026-09-04T13:30:00Z"
  }
}
```

#### Technical Notes

  - WebSocket authentication uses the same SimpleJWT access token as the REST API
  - Token is passed as query parameter due to browser WebSocket header limitations
  - Real-time delivery is best-effort and fail-safe
  - Database notification persistence remains the source of truth
  - Tests avoid Redis by monkeypatching the channel layer with InMemoryChannelLayer
  - A harmless teardown warning may appear in tests due to Channels' internal receive task cleanup

#### Next Steps

  - Add WebSocket heartbeat/ping-keepalive
  - Add client reconnect/backoff strategy
  - Add browser/desktop notification integration
  - Add unread notification count subscription
  - Add per-user notification preferences
  - Add Redis-backed channel layer configuration for staging/production validation
  - Add integration tests with real Redis if needed
