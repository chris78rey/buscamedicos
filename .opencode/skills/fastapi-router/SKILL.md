---
name: fastapi-router
description: 'FastAPI router creation pattern for BuscaMedicos. 30+ routers with consistent structure, auth, and error handling.'
license: MIT
---

# FastAPI Router Skill

## Overview

FastAPI router creation pattern for BuscaMedicos. All routers follow a consistent structure with async/await, SQLAlchemy async sessions, and JWT auth.

## When to Use

Use this skill when:
- Creating a new API endpoint
- Adding a new router file
- Modifying existing endpoint logic

## Router Pattern

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/{domain}", tags=["domain-tag"])


@router.get("/resource")
async def list_resource(
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Model).offset(offset).limit(limit))
    return result.scalars().all()
```

## Key Conventions

| Aspect | Convention |
|--------|------------|
| Prefix | `/api/v1/{actor}/{resource}` (e.g., `/api/v1/patient/appointments`) |
| Tags | kebab-case (e.g., `patient-clinical`) |
| Auth | `Depends(get_current_user)` returns `User` |
| DB | `AsyncSession = Depends(get_db)` |
| Pagination | `limit: Query(20, le=100), offset: Query(0)` |
| Response | Pydantic schema from `app.schemas.stepN_schemas` |

## Error Handling

```python
from fastapi import HTTPException, status

@router.get("/{resource_id}")
async def get_resource(resource_id: str, ...):
    result = await db.execute(select(Model).where(Model.id == resource_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Resource not found")
    return obj
```

## Router Registration

1. Add import in `app/routers/__init__.py`
2. Add `include_router` in `app/main.py` with prefix and tags

```python
# In main.py
from app.routers import new_router
app.include_router(new_router, prefix="/api/v1", tags=["new-tag"])
```

## Common Patterns

### POST with body
```python
from pydantic import BaseModel

class CreateResource(BaseModel):
    name: str
    description: Optional[str] = None

@router.post("/resource", response_model=ResourceResponse)
async def create_resource(
    data: CreateResource,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ...
```

### Conditional query params
```python
@router.get("/resource")
async def list_resource(
    name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Model)
    if name:
        query = query.where(Model.name == name)
    result = await db.execute(query)
    return result.scalars().all()
```
