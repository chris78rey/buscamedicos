---
name: fastapi-error-handling
description: 'Error handling patterns for BuscaMedicos FastAPI. HTTPException, custom exceptions, and consistent error response format.'
license: MIT
---

# FastAPI Error Handling Skill

## Overview

Error handling patterns for BuscaMedicos. Consistent error responses, custom exception classes, and proper HTTP status codes.

## When to Use

Use this skill when:
- Adding error handling to endpoints
- Creating custom exceptions
- Standardizing error response format

## HTTPException Pattern

```python
from fastapi import HTTPException, status

@router.get("/{resource_id}")
async def get_resource(resource_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Model).where(Model.id == resource_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    return obj
```

## Common Status Codes

| Code | Use Case |
|------|----------|
| 400 | Bad request / validation error |
| 401 | Unauthorized (no/invalid auth) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource not found |
| 409 | Conflict (duplicate resource) |
| 422 | Validation error (Pydantic) |
| 500 | Internal server error |

## Custom Exception Classes

```python
class NotFoundError(Exception):
    def __init__(self, resource: str, resource_id: str):
        self.resource = resource
        self.resource_id = resource_id

class DuplicateResourceError(Exception):
    def __init__(self, resource: str, identifier: str):
        self.resource = resource
        self.identifier = identifier
```

## Error Response Format

```python
from fastapi.responses import JSONResponse

@router.get("/error-example")
async def error_example():
    return JSONResponse(
        status_code=400,
        content={"detail": "Error message", "code": "ERROR_CODE"}
    )
```

## Validation Errors

Pydantic automatically returns 422 for validation failures with this format:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Global Exception Handler

Add to `main.py`:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "detail": f"{exc.resource} {exc.resource_id} not found",
            "code": "NOT_FOUND"
        }
    )
```

## Gotchas

- DO NOT use empty `except Exception: pass` - always log or handle properly
- DO NOT suppress errors - let them propagate with appropriate status codes
- Always provide meaningful error messages in `detail` field
