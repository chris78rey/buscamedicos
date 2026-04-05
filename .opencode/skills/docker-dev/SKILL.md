---
name: docker-dev
description: 'Docker Compose development workflow for BuscaMedicos. Start/stop/verify containers, check logs, rebuild with --build flag.'
license: MIT
---

# Docker Dev Skill

## Overview

Docker Compose workflow for the BuscaMedicos project. Uses `infra/docker-compose.yml` with `--profile required` for local development.

## When to Use

Use this skill when:
- Starting local development environment
- Rebuilding after dependency changes
- Checking container health and logs
- Verifying the backend is responding

## Quick Commands

```bash
# Start services
docker compose -f infra/docker-compose.yml --profile required up -d

# Rebuild after changes
docker compose -f infra/docker-compose.yml up -d --build

# Stop services
docker compose -f infra/docker-compose.yml down

# Validate compose config
docker compose -f infra/docker-compose.yml config --quiet
```

## Health Check

```bash
curl http://localhost:8000/health/live
# Returns: {"status":"ok"}
```

## Container Names

| Service | Container | Port |
|---------|-----------|------|
| Backend | `buscamedicos_backend` | 8000 |
| Postgres | `buscamedicos_postgres` | 5432 |

## Common Workflows

### Rebuild after requirements.txt change
```bash
docker compose -f infra/docker-compose.yml up -d --build
```

### Check backend logs
```bash
docker logs buscamedicos_backend --tail 50
```

### Run migrations in container
```bash
docker exec buscamedicos_backend sh -c "cd /app && PYTHONPATH=/app alembic upgrade head"
```

### Run seed in container
```bash
docker exec buscamedicos_backend sh -c "cd /app && PYTHONPATH=/app python scripts/seed.py"
```

## Gotchas

- The local compose uses `../backend_api` context paths (from `infra/`)
- Health check: `curl -f http://localhost:8000/health/live || exit 1` inside container
- Postgres data persists in `postgres_data` volume
- Use `docker compose` from `infra/` directory
