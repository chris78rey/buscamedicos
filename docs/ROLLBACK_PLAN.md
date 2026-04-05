# Rollback Plan

## When to Rollback
- Critical bug affecting production data
- Security vulnerability actively exploited
- Service completely unavailable after failed deploy
- Database corruption discovered post-deploy

## When NOT to Rollback
- Minor bugs with workarounds
- Non-critical cosmetic issues
- Performance degradation (prefer scaling first)
- Single user reporting issues

## Rollback Procedure

### Step 1: Assess
```bash
# Check current health
curl http://localhost:8000/health/ready

# Check recent logs
docker compose -f docker-compose.prod.yml logs --tail=100 backend_api

# Identify the issue
./scripts/smoke_test.sh
```

### Step 2: Protect Current State
```bash
# Create emergency backup of current DB
docker exec buscamedicos_postgres pg_dump -Fc -f /tmp/emergency_backup.dump buscamedicos

# Copy to host
docker cp buscamedicos_postgres:/tmp/emergency_backup.dump ../backups/emergency_pre_rollback_$(date +%Y%m%d_%H%M%S).dump
```

### Step 3: Register Rollback
```bash
# Get current release ID
curl http://localhost:8000/api/v1/admin/ops/releases

# Mark current as rolled back
curl -X POST http://localhost:8000/api/v1/admin/ops/releases/<current_id>/mark-rollback
```

### Step 4: Redeploy Previous Version
```bash
# Get previous image tag
docker images buscamedicos-backend

# Stop current
docker compose -f docker-compose.prod.yml stop backend_api

# Start with previous image (manually edit docker-compose.prod.yml or use specific tag)
IMAGE_TAG=<previous_tag> docker compose -f docker-compose.prod.yml up -d
```

### Step 5: Verify
```bash
curl http://localhost:8000/health/ready
./scripts/smoke_test.sh
```

### Step 6: Post-Rollback
- [ ] Document incident
- [ ] Notify stakeholders
- [ ] Analyze root cause
- [ ] Plan fix before next deploy

## Rollback via Docker Image Tag
The `docker-compose.prod.yml` uses `IMAGE_TAG` environment variable:
```bash
export IMAGE_TAG=v0.9.0  # previous working version
docker compose -f docker-compose.prod.yml up -d --no-deps backend_api
```
