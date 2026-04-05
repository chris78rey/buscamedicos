---
name: pydantic-schemas
description: 'Pydantic v2 schema creation for BuscaMedicos. Request/response models, validation, and step-based schema organization.'
license: MIT
---

# Pydantic Schemas Skill

## Overview

Pydantic v2 schema creation for BuscaMedicos. Request/response models organized by step (step2-step8), with validation and email support.

## When to Use

Use this skill when:
- Creating request/response models
- Adding validation to endpoints
- Defining API contracts

## Schema Pattern

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class ResourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    description: Optional[str] = None

class ResourceResponse(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
```

## Step Organization

| Step | Schema File | Content |
|------|------------|---------|
| step2 | step2_schemas.py | Specialty, Appointment schemas |
| step3 | step3_schemas.py | Payment, pricing schemas |
| step4 | step4_schemas.py | Clinical record schemas |
| step6 | step6_schemas.py | Moderation schemas |
| step7 | step7_schemas.py | Privacy, consent schemas |
| step8 | step8_schemas.py | Operational schemas |

## Field Validation

```python
from pydantic import Field, validator

class CreateModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., pattern=r"^[A-Z]{3}$")  # 3 uppercase letters
    count: int = Field(default=0, ge=0)  # >= 0
    email: EmailStr  # Validates email format
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('name cannot be empty')
        return v.strip()
```

## Response Models

```python
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}

class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    limit: int
    offset: int
```

## Request/Response Cycle

```python
from fastapi import Depends

@router.post("/resource", response_model=ResourceResponse)
async def create_resource(
    data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
):
    # data is validated ResourceCreate
    # response is serialized ResourceResponse
```

## Optional Fields

```python
class UpdateResource(BaseModel):
    name: Optional[str] = None  # Can be omitted
    description: Optional[str] = Field(default=None, max_length=500)
```

## Gotchas

- Use `EmailStr` from pydantic (requires `pydantic[email]` extra)
- `model_config = {"from_attributes": True}` needed to parse ORM objects
- Enums serialize as strings by default in Pydantic v2
- `Field(...)` with no default means required
