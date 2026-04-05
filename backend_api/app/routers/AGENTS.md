# Routers Module

**Parent:** `backend_api/app/`

## OVERVIEW

30+ API endpoint modules organized by domain. All imported in `__init__.py` and registered in `main.py`.

## WHERE TO LOOK

| Router | Path | Notes |
|--------|------|-------|
| auth | `auth.py` | Login, register, refresh |
| patients | `patients.py` | Patient profile |
| professionals | `professionals.py` | Professional search/profile |
| patient_appointments | `patient_appointments.py` | Booking flow |
| patient_clinical | `patient_clinical.py` | Clinical records access |
| patient_privacy | `patient_privacy.py` | Privacy consent |
| admin_moderation | `admin_moderation.py` | Reviews, sanctions |
| admin_privacy | `admin_privacy.py` | Privacy policies |
| ops | `ops.py` | Health, backups, releases |
| privacy_auditor | `privacy_auditor.py` | Access log export |

## PATTERN

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/path", tags=["tag"])

@router.get("/endpoint")
async def handler(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ...
```

## CONVENTIONS

- Prefix format: `/api/v1/{domain}` or `/api/v1/{actor}/{domain}`
- Tags match folder structure: `patient-clinical`, `admin-privacy`
- All routers use async/await with `AsyncSession`
- Auth dependency: `get_current_user` returns `User`

## LARGE FILES (>200 lines)

| File | Lines | Purpose |
|------|-------|---------|
| ops.py | 673 | Health, deployments, backups |
| admin_moderation.py | 560 | Reviews, reports, sanctions |
| admin_privacy.py | 582 | Privacy policies, exceptional access |
| professional_clinical.py | 420 | Clinical notes, prescriptions |
