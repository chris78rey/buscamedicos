# BuscaMedicos - Marketplace de Salud Ecuador

## Quick Start

### Requirements
- Docker & Docker Compose
- Python 3.11+

### Backend Setup

```bash
cd backend_api
cp ../infra/.env.example .env
pip install -r requirements.txt
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

### Docker Compose

```bash
cd infra
cp .env.example .env
docker compose --profile required up -d
```

### Run Tests

```bash
cd backend_api
pytest tests/ -v
```

## Structure

```
buscamedicos/
├── app_flutter/          # Flutter mobile app
├── backend_api/          # FastAPI backend
│   ├── app/
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routers/      # API endpoints
│   │   └── core/         # Config, security, database
│   ├── alembic/          # Database migrations
│   └── tests/            # Test suite
├── infra/                # Docker, env examples
├── docs/                 # Documentation
├── scripts/              # Seeds and utilities
└── contracts/            # API schemas
```

## API Endpoints

### Auth
- POST /api/v1/auth/register/patient
- POST /api/v1/auth/register/professional
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- GET /api/v1/auth/me

### Admin
- GET /api/v1/admin/verification-requests
- POST /api/v1/admin/verification-requests/{id}/approve
- POST /api/v1/admin/verification-requests/{id}/reject

## Environment Variables

See infra/.env.example for configuration.