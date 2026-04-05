# Production Deployment Guide

## Prerequisites
- Single VPS with Docker and Docker Compose installed
- Domain name pointed to VPS IP
- PostgreSQL client tools (`pg_dump`, `pg_restore`)

## Environment Setup

```bash
cd infra
cp .env.production.example .env.production
# Edit .env.production with real values
```

Generate secrets:
```bash
openssl rand -hex 32  # for SECRET_KEY
openssl rand -base64 24  # for POSTGRES_PASSWORD
```

## Deployment Steps

### 1. Initial Setup
```bash
# Build Docker image
docker build -f backend_api/Dockerfile.prod -t buscamedicos-backend:v1.0.0 ../backend_api

# Start services
docker compose -f docker-compose.prod.yml up -d

# Run migrations
docker exec buscamedicos_backend python -m alembic upgrade head

# Seed data
docker exec buscamedicos_backend python scripts/seed.py

# Smoke test
./scripts/smoke_test.sh
```

### 2. Register Release
```bash
curl -X POST http://localhost:8000/api/v1/admin/ops/releases/register \
  -H "Content-Type: application/json" \
  -d '{"release_code": "v1.0.0", "image_tag": "v1.0.0", "environment": "production"}'
```

### 3. Configure Domain
Point your domain A record to the VPS IP. Caddy will automatically obtain TLS certificates.

## Docker Compose Profiles
- `required`: Always running (postgres, backend, caddy)
- Default: Same as `required` in production

## Health Checks
- `GET /health/live` — liveness probe
- `GET /health/ready` — readiness probe (checks DB, storage)
- `GET /health/details` — detailed status (admin only)

## Rollback
```bash
./scripts/rollback.sh <release_id>
# Then redeploy previous image tag
```

## Monitoring
```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f

# Check health
curl http://localhost:8000/health/ready
```

## Backup
```bash
./scripts/backup_db.sh
./scripts/backup_files.sh
```

## Restore Test
```bash
./scripts/restore_test.sh ../backups/pg_dump_YYYYMMDD_HHMMSS.dump
```
