# Phase 10: Reporting & Analytics - Deliverables

## Status: COMPLETE ✅

## Summary
Phase 10 introduces reporting and analytics capabilities through a dedicated `reporting` app. All metrics are computed on the fly from existing models (no new database tables), providing a real-time dashboard of system-wide counts and an activity feed derived from the audit log.

## Deliverables

### 1. Reporting Service (`apps/reporting/services/reporting_service.py`)

#### Dashboard Metrics
`get_dashboard_metrics()` returns aggregated counts across all domains:

- **Proposals**: Total and counts by status
- **Agreements**: Total and counts by status
- **Negotiations**: Total and counts by status
- **Notifications**: Total, unread, read, archived
- **Agents**: Total agents, active agents, total rules, active rules
- **Jobs**: Total, counts by status, and success rate
- **generated_at**: ISO timestamp of metric generation

#### Activity Feed
`get_activity_feed(limit)` returns recent audit log entries as a list of dictionaries with id, action, entity_type, entity_id, actor_id, and created_at.

### 2. Serializers (`apps/reporting/serializers/`)

- **DashboardSerializer**: Full dashboard structure with nested serializers
- **StatusCountSerializer**: Reusable for proposals/agreements/negotiations
- **NotificationCountSerializer**: Notification counts
- **AgentCountSerializer**: Agent and rule counts
- **JobCountSerializer**: Job counts with success rate
- **ActivityEntrySerializer**: Single activity feed entry

These serializers are descriptive (read-only) and serve both validation and API documentation purposes.

### 3. API Endpoints

#### Dashboard (`/api/reporting/dashboard/`)
- `GET /api/reporting/dashboard/` - Returns aggregated system metrics
- Read-only, requires authentication

#### Activity Feed (`/api/reporting/activity/`)
- `GET /api/reporting/activity/` - Returns recent activity entries
- `GET /api/reporting/activity/?limit=N` - Configurable limit (1-100, default 20)
- Read-only, requires authentication

### 4. Views (`apps/reporting/views/`)

- **DashboardView**: APIView returning dashboard metrics
- **ActivityFeedView**: APIView with limit parsing and validation

Both views use `@extend_schema` decorators for proper drf-spectacular documentation.

### 5. Test Coverage

#### Service Tests
- Dashboard returns all sections
- Per-domain counts are accurate
- Success rate calculation (including zero-finished edge case)
- Activity feed returns entries, respects limit, and orders by created_at desc

#### API Tests
- Dashboard returns 200 with expected structure
- Dashboard reflects actual data counts
- Activity feed returns 200, respects limit, caps at max, handles invalid limit
- Authentication requirements (401)

**Coverage:** 94%+ across the reporting service

### 6. Key Features

✅ **No new models**: Metrics computed on the fly from existing data

✅ **Efficient aggregation**: Single query per domain using `values().annotate(Count())`

✅ **Success rate**: Computed as COMPLETED / (COMPLETED + FAILED) percentage

✅ **Configurable activity feed**: Limit parameter with validation and max cap

✅ **Read-only endpoints**: Reports are queryable but not modifiable

✅ **API documentation**: Full schema via drf-spectacular with `@extend_schema`

## API Usage Examples

### Get Dashboard Metrics
```bash
GET /api/reporting/dashboard/

Response:
{
  "proposals": {"total": 15, "by_status": {"DRAFT": 5, "APPROVED": 8, "EXECUTED": 2}},
  "agreements": {"total": 7, "by_status": {"ACTIVE": 4, "COMPLETED": 3}},
  "negotiations": {"total": 3, "by_status": {"IN_PROGRESS": 1, "AGREED": 2}},
  "notifications": {"total": 42, "unread": 5, "read": 30, "archived": 7},
  "agents": {"total_agents": 2, "active_agents": 2, "total_rules": 5, "active_rules": 4},
  "jobs": {"total": 120, "by_status": {"COMPLETED": 110, "FAILED": 10}, "success_rate": 91.67},
  "generated_at": "2026-09-07T12:00:00+00:00"
}
```

### Get Activity Feed
```bash
GET /api/reporting/activity/?limit=10

Response:
[
  {
    "id": "uuid",
    "action": "PROPOSAL_CREATED",
    "entity_type": "Proposal",
    "entity_id": "uuid",
    "actor_id": "uuid",
    "created_at": "2026-09-07T11:55:00+00:00"
  }
]
```

#### Technical Notes

  - All metrics use values().annotate(Count()) for single-query aggregation per domain
  - Success rate guards against division by zero when no jobs have finished
  - Activity feed limit is parsed defensively and capped at 100
  - @extend_schema decorators resolve drf-spectacular's APIView serializer inference
  - Type hints throughout (mypy strict compliant)
  - Google-style docstrings on all functions and classes

#### Next Steps (Phase 11)

  - Add webhooks for external system integration
  - Implement outbound event subscriptions
  - Add API rate limiting and throttling
  - Build frontend dashboard consuming these endpoints
  - Add export capabilities (CSV/JSON)
  - Add time-series metrics (counts over time periods)

#### Performance Considerations

  - Aggregation queries are optimized with values().annotate(Count())
  - Activity feed limited to 100 entries max to prevent overload
  - No N+1 queries in reporting endpoints
  - Metrics computed on demand (no stale cache) - consider caching if load increases
