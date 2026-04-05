# BuscaMedicos - PROJECT KNOWLEDGE BASE

**Generated:** 2026-04-05
**Type:** FastAPI Backend + Flutter Mobile App
**Stack:** Python 3.11+ / FastAPI / SQLAlchemy (async) / PostgreSQL / Docker

## OVERVIEW

Health marketplace for Ecuador connecting patients with medical professionals. Backend is a multi-domain FastAPI monolith with step-by-step architecture (step2 through step8 models).

## STRUCTURE

```
buscamedicos/
├── backend_api/           # FastAPI + SQLAlchemy async + Alembic migrations
│   ├── app/
│   │   ├── routers/      # 30+ API endpoint modules
│   │   ├── models/       # 22 SQLAlchemy models (step2-step8)
│   │   ├── services/     # 5 service modules
│   │   ├── schemas/      # Pydantic request/response models
│   │   └── core/        # Database, config, security, dependencies
│   ├── alembic/versions/ # DB migrations
│   ├── scripts/          # Seed scripts
│   └── tests/
├── app_flutter/          # Flutter mobile app
├── infra/                # Docker Compose, env examples
├── docs/                 # Documentation
└── pasos/                # Deployment steps
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new model | `backend_api/app/models/stepN_models.py` | Follow step-architecture |
| Add new router | `backend_api/app/routers/` | Use existing router pattern |
| Add service logic | `backend_api/app/services/stepN_services.py` | One service per step |
| Database migration | `backend_api/alembic/versions/` | `alembic revision --autogenerate` |
| API schemas | `backend_api/app/schemas/` | Pydantic models |
| Docker deploy | `infra/docker-compose.yml` | Local dev profile |

## ARCHITECTURE PATTERNS

### Step-Based Incremental Development
- Models: `step2_models.py` → `step3_models.py` → ... → `step8_models.py`
- Services: `step2_services.py` → `step3_services.py` → ... → `step7_services.py`
- Schemas: `step2_schemas.py` → ... → `step8_schemas.py`
- **NEVER import from future steps** (step8 cannot import from step7)

### Router Organization
- 30+ routers organized by domain (patients, professionals, admin, privacy, etc.)
- All routers imported in `backend_api/app/routers/__init__.py`
- Included in `app/main.py` with prefix and tags

### Model Conventions
- Base class: `from app.core.database import Base`
- ID: `Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))`
- Timestamps: `Column(DateTime, default=datetime.utcnow)`
- Enums: `import enum; class Foo(str, enum.Enum)`

## CONVENTIONS

- **Database**: PostgreSQL 16 with `asyncpg` driver
- **ORM**: SQLAlchemy 2.0 with async sessions
- **Migrations**: Alembic (run `alembic upgrade head` after model changes)
- **Auth**: JWT via `python-jose`, password hashing via `passlib`
- **Validation**: Pydantic v2 with `email` extra for email fields
- **Docker**: Multi-stage build, `backend_api/Dockerfile`

## ANTI-PATTERNS (THIS PROJECT)

- DO NOT use `datetime.utcnow()` without import (already imported in models)
- DO NOT create duplicate table definitions (check `step7_models.py` before adding)
- DO NOT import `Professional` from `step2_models` (exists in `professional.py`)
- DO NOT use `as any` or `@ts-ignore` (type safety required)
- DO NOT skip error handling with empty `catch(e) {}`

## COMMANDS

```bash
# Local dev (outside Docker)
cd backend_api
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Docker dev
cd infra
docker compose --profile required up -d

# Tests
cd backend_api
pytest tests/ -v
```

## NOTES

- `backend_api/app/main.py` is the ONLY entry point
- All 30+ routers registered in `app/main.py` with prefixes
- Health check: `GET /health/live` returns `{"status":"ok"}`
- Step migrations must run sequentially (step2 → step3 → ... → step8)

## LOCAL SKILLS

Project-specific skills available in `.skills/`:

| Skill | Use When |
|-------|----------|
| `alembic-migrations` | Adding models, running migrations |
| `docker-dev` | Docker Compose start/stop/rebuild |
| `fastapi-router` | Creating new API endpoints |
| `fastapi-error-handling` | Error handling in endpoints |
| `pydantic-schemas` | Request/response models |
| `sqlalchemy-models` | Database model patterns |
| `buscamedicos-testing` | Writing tests with pytest |

**Loading a skill:** `skill(name="alembic-migrations")`
