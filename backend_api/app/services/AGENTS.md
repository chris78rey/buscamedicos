# Services Module

**Parent:** `backend_api/app/`

## OVERVIEW

Business logic layer. 5 service modules with ~3200 lines total. All use async/await with SQLAlchemy AsyncSession.

## WHERE TO LOOK

| File | Lines | Purpose |
|------|-------|---------|
| `step7_services.py` | 1290 | Privacy, consent, clinical access |
| `step6_services.py` | 852 | Moderation, reviews, sanctions |
| `step4_services.py` | 548 | Teleconsultation, clinical notes |
| `step3_services.py` | 306 | Payments, settlements |
| `step2_services.py` | 191 | Appointments, slots |

## PATTERN

```python
class ServiceName:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def method(self, param: str) -> ResultType:
        result = await self.db.execute(select(Model).where(...))
        return result.scalar_one_or_none()
```

## KEY SERVICES

- `ModerationAuditService` (step6) - logs audit events via `AuditEvent`
- `ClinicalAccessLoggingService` (step7) - exports access logs metadata only
- `ExceptionalAccessRequestService` (step7) - privacy exceptional access workflow
- `ContextualAccessDecisionService` (step7) - evaluates access policies

## NOTE

Services create `AuditEvent` records but field names may differ from ORM model:
- Use `user_id` not `actor_user_id`
- Use `resource_type` not `entity_type`
- Use `metadata_json` not `before_json`
See `audit.py` model for actual field names.
