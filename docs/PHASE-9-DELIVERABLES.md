# Phase 9: Scheduled Automation - Deliverables

## Status: COMPLETE ✅

## Summary
Phase 9 introduces scheduled task execution using Celery, enabling the system to run automation rules on a schedule, perform periodic maintenance, and record a full history of automated executions. The `ON_SCHEDULE` trigger from Phase 8 is now fully functional, with tasks running periodically via Celery Beat.

## Deliverables

### 1. Celery Configuration

#### Celery App (`legatio/celery.py`)
- Celery app instance with namespace `CELERY`
- Auto-discovery of tasks in all installed apps
- Settings loaded from Django settings with `CELERY_` prefix

#### Beat Schedule (`legatio/settings/base.py`)
- `process-scheduled-rules`: Every 5 minutes
- `check-expired-agreements`: Every hour
- `cleanup-old-jobs`: Every 24 hours (retains 90 days)

### 2. Models

#### ScheduledJob (`apps/scheduling/models/scheduled_job.py`)
- UUID primary key
- Name and task_name
- Status lifecycle: PENDING → RUNNING → COMPLETED / FAILED / SKIPPED
- Optional link to AutomationRule (SET_NULL on delete)
- Timing fields: scheduled_for, started_at, finished_at
- JSON result and error message
- Timestamps (created_at, updated_at)
- Properties: `is_finished`, `succeeded`, `duration_seconds`

### 3. Service Layer

#### SchedulingService (`apps/scheduling/services/scheduling_service.py`)
- `create_job()`: Creates a PENDING job record
- `mark_running()`: Sets RUNNING status and started_at
- `mark_completed()`: Sets COMPLETED status, finished_at, and result
- `mark_failed()`: Sets FAILED status, finished_at, and error
- `mark_skipped()`: Sets SKIPPED status with reason

### 4. Celery Tasks

#### `apps/agents/tasks.py`
- `ping()`: Health-check task
- `process_scheduled_rules()`: Finds and executes all active ON_SCHEDULE rules, recording each as a ScheduledJob

#### `apps/scheduling/tasks.py`
- `check_expired_agreements()`: Terminates active agreements past expiration date
- `cleanup_old_jobs()`: Deletes old completed/failed/skipped job records

### 5. API Endpoints

#### ScheduledJob API (`/api/scheduling/jobs/`) - Read-only
- `GET /api/scheduling/jobs/` - List jobs (paginated, filterable)
- `GET /api/scheduling/jobs/{id}/` - Retrieve a specific job
- Filters: `status`, `task_name`, `automation_rule`
- **No create/update/delete** (405 Method Not Allowed) - jobs are system-created

### 6. Admin Interface (`apps/scheduling/admin.py`)

#### ScheduledJobAdmin
- Read-only (jobs are system-created)
- Delete allowed for manual cleanup
- List display with duration column
- Filtering by status, task_name, scheduled_for
- Search by name, task_name, error
- Optimized queryset with select_related

### 7. Test Coverage

#### Model Tests
- ScheduledJob creation, properties, ordering

#### Service Tests
- Job creation and status transitions (running, completed, failed, skipped)
- Nonexistent job error handling

#### Task Tests
- ping health-check
- process_scheduled_rules (executes matching, skips inactive, records failures)
- check_expired_agreements (terminates expired, preserves active/future)
- cleanup_old_jobs (deletes old, preserves recent/pending)

#### API Tests
- List/retrieve operations
- Filtering by status and task_name
- Access restrictions (405 for create/update/delete)
- Authentication requirements (401)

**Coverage:** 90%+ across the scheduling app

### 8. Key Features

✅ **Scheduled Execution**: ON_SCHEDULE rules run automatically every 5 minutes
✅ **Execution History**: Full audit trail of automated job runs
✅ **Expiration Handling**: Agreements auto-terminated when they expire
✅ **Data Retention**: Old job records cleaned up automatically
✅ **Fail-Safe**: Individual rule failures don't block other rules
✅ **Read-Only API**: Job history queryable but not modifiable via API
✅ **Monitoring**: Admin shows execution durations for debugging

## Running the System

To run the full system with scheduled tasks:

### 1. Start Redis (broker)
```bash
redis-server
```

### 2. Start Celery worker
```bash
cd backend
celery -A legatio worker --loglevel=info
```

### 3. Start Celery Beat (scheduler)
```bash
cd backend
celery -A legatio beat --loglevel=info
```

### 4. Start Django
```bash
python manage.py runserver
```

### Verify Celery is working
```bash
# From Django shell
python manage.py shell
>>> from apps.agents.tasks import ping
>>> ping.delay().get(timeout=5)
'pong'
```

#### Technical Notes

  - Tasks use local imports to avoid loading Django models before initialization
  - Each scheduled rule execution creates a ScheduledJob record for auditability
  - Job records are cleaned up after 90 days to keep the table manageable
  - Type hints throughout (mypy strict compliant)
  - Google-style docstrings on all functions and classes

#### Next Steps (Phase 10)

  - Build reporting/analytics endpoints (dashboards, metrics)
  - Add webhook endpoints for external trigger sources
  - Implement APPROVE_PROPOSAL and REJECT_PROPOSAL automation actions
  - Add rate limiting for agent actions
  - Build frontend for job monitoring
  - Add integration tests with real Redis

#### Performance Considerations

  - Optimized queries with select_related on foreign keys
  - Indexes on frequently filtered fields (status, scheduled_for, task_name)
  - Paginated list endpoints for large datasets
  - Periodic cleanup prevents unbounded table growth
