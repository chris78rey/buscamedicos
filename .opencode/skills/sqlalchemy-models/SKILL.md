---
name: sqlalchemy-models
description: 'SQLAlchemy model creation for BuscaMedicos. Step-architecture pattern (step2-step8), async sessions, and model conventions.'
license: MIT
---

# SQLAlchemy Models Skill

## Overview

SQLAlchemy 2.0 async model creation for BuscaMedicos. Uses step-based architecture - new models go in the appropriate `stepN_models.py` file.

## When to Use

Use this skill when:
- Creating new database models
- Adding columns to existing models
- Understanding model relationships

## Step Architecture

| Step | File | Content |
|------|------|---------|
| step2 | step2_models.py | Core: Specialty, Appointment, ProfessionalPublicProfile |
| step3 | step3_models.py | Payments: PricingPolicy, PaymentIntent, Settlement |
| step4 | step4_models.py | Clinical: TeleconsultationSession, Prescription |
| step6 | step6_models.py | Moderation: Review, SafetyReport, Sanction |
| step7 | step7_models.py | Privacy: DataClassification, ResourceAccessPolicy, ExceptionalAccessRequest |
| step8 | step8_models.py | Operations: DeploymentRelease, OperationalJob, BackupArtifact |

## Model Pattern

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.orm import DeclarativeBase
import enum

class Base(DeclarativeBase):
    pass

class MyStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class MyModel(Base):
    __tablename__ = "my_table"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    status = Column(String, default=MyStatus.ACTIVE.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")
```

## Key Conventions

| Aspect | Convention |
|--------|------------|
| ID | `Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))` |
| Timestamps | Use `datetime.utcnow` (imported at file top) |
| Soft delete | `deleted_at = Column(DateTime, nullable=True)` |
| Versioning | `version = Column(String, default="1")` |
| Enum | `class MyEnum(str, enum.Enum):` |

## Common Mistakes to Avoid

1. **Wrong import for Professional**
   ```python
   # WRONG
   from app.models.step2_models import Professional
   
   # RIGHT
   from app.models.professional import Professional
   ```

2. **Missing datetime import**
   ```python
   # WRONG - datetime.utcnow used but not imported
   created_at = Column(DateTime, default=datetime.utcnow)
   
   # RIGHT
   from datetime import datetime
   created_at = Column(DateTime, default=datetime.utcnow)
   ```

3. **Duplicate table definitions**
   - Check `step7_models.py` before adding privacy-related models
   - `ExceptionalAccessRequest` already exists in `step7_models.py`

## Relationships

```python
# One-to-many
class Parent(Base):
    __tablename__ = "parent"
    id = Column(String, primary_key=True)
    children = relationship("Child", back_populates="parent")

class Child(Base):
    __tablename__ = "child"
    id = Column(String, primary_key=True)
    parent_id = Column(String, ForeignKey("parent.id"))
    parent = relationship("Parent", back_populates="children")
```

## Indexes

```python
# Single column
Column(String, nullable=False, index=True)

# Multi-column
Index('ix_name', 'col1', 'col2')
```
