# Models Module

**Parent:** `backend_api/app/`

## OVERVIEW

22 SQLAlchemy models organized by step (step2-step8). Step architecture enforces forward-compatibility.

## WHERE TO LOOK

| File | Models | Notes |
|------|--------|-------|
| `user.py` | User | Auth主体 |
| `professional.py` | Professional | 医生 entity |
| `patient.py` | Patient | 患者 entity |
| `role.py` | Role, UserRole | 权限模型 |
| `step2_models.py` | Specialty, Appointment, ProfessionalPublicProfile | 核心业务 |
| `step7_models.py` | Privacy models, ExceptionalAccessRequest | 隐私相关 |
| `step8_models.py` | Operational models | 运维表 |

## STEP ARCHITECTURE

```
step2: Core booking (Specialty, Appointment, ProfessionalPublicProfile)
step3: Payments (PricingPolicy, PaymentIntent, Settlement)
step4: Clinical (TeleconsultationSession, Prescription, ClinicalNote)
step5: (not used)
step6: Moderation (AppointmentReview, SafetyReport, AccountSanction)
step7: Privacy (DataClassification, ResourceAccessPolicy, PrivacyIncident)
step8: Operations (DeploymentRelease, OperationalJob, BackupArtifact)
```

## ANTI-PATTERNS

- **DO NOT** import `Professional` from `step2_models` - it's in `professional.py`
- **DO NOT** define same table in multiple step files
- **DO NOT** use `datetime.utcnow` without `from datetime import datetime`
- `ExceptionalAccessRequest` belongs to `step7_models.py`, NOT `system.py`

## MODEL PATTERN

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.core.database import Base
import enum

class MyEnum(str, enum.Enum):
    VALUE = "value"

class MyModel(Base):
    __tablename__ = "my_table"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## RELATIONSHIPS

- User → Patient (one-to-one)
- User → Professional (one-to-one)
- Professional → ProfessionalDocument (one-to-many)
- Appointment → AppointmentReview (one-to-many)
