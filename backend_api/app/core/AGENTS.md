# Core Module

**Parent:** `backend_api/app/`

## OVERVIEW

Database, configuration, security, and dependency injection. Only 13 lines for database setup.

## WHERE TO LOOK

| File | Purpose |
|------|---------|
| `database.py` | Async engine, session maker, Base class |
| `config.py` | Pydantic settings from env |
| `dependencies.py` | `get_current_user`, auth utilities |
| `security.py` | Password hashing, JWT handling |

## DATABASE PATTERN

```python
# database.py - only 13 lines
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session_maker() as session:
        yield session
```

## AUTH FLOW

1. `security.py` - `Hash` (bcrypt), `create_access_token` (jose)
2. `dependencies.py` - `get_current_user` extracts JWT from header
3. Routers use `Depends(get_current_user)` to protect endpoints

## SETTINGS

Settings loaded from env vars via `pydantic-settings`:
- `DATABASE_URL` (required)
- `SECRET_KEY` (required)
- `DEBUG` (bool)
- `APP_ENV` (development/production)
