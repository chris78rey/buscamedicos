# Incident Runbook

## Backend Down
**Symptoms**: Health endpoint returns 5xx, container not responding

**Diagnosis**:
```bash
docker compose -f docker-compose.prod.yml logs backend_api
docker compose -f docker-compose.prod.yml ps
```

**Fix**:
```bash
docker compose -f docker-compose.prod.yml restart backend_api
```

**If still failing**: Check disk space, memory, and database connectivity.

## Database Unreachable
**Symptoms**: `/health/ready` returns `database: not_ready`

**Diagnosis**:
```bash
docker compose -f docker-compose.prod.yml logs postgres
docker exec buscamedicos_postgres pg_isready
```

**Fix**: Restart postgres container or restore from latest backup.

## Disk Full
**Symptoms**: Write operations fail, containers exit

**Diagnosis**:
```bash
df -h
docker system df
```

**Fix**:
```bash
docker system prune -a
docker volume prune
rm -rf ../backups/*  # Remove old backups first
```

## TLS Certificate Issues
**Symptoms**: HTTPS not working, certificate errors

**Fix**: Caddy auto-renews. If stuck:
```bash
docker exec buscamedicos_caddy caddyificates
docker compose -f docker-compose.prod.yml restart caddy
```

## Backup Failed
**Symptoms**: Backup job shows `failed` status

**Diagnosis**:
```bash
docker exec buscamedicos_backend python -c "from app.services.step8_services import BackupService; ..."
```

**Fix**: Check disk space and DATABASE_URL configuration.

## Restore Failed
**Symptoms**: Restore test returns error

**Fix**: Verify backup file exists and is valid:
```bash
./scripts/restore_test.sh ../backups/pg_dump_LATEST.dump
ls -la ../backups/
```

## Rate Limit Triggered
**Symptoms**: Users getting 429 responses

**Diagnosis**:
```bash
curl http://localhost:8000/api/v1/admin/ops/rate-limit-events
```

**Fix**: Wait for cooldown window, or disable rate limiting via feature flag.

## Security Incident
1. Isolate affected container: `docker network disconnect internal <container>`
2. Rotate all secrets in `.env.production`
3. Redeploy: `docker compose -f docker-compose.prod.yml up -d --force-recreate`
4. Review audit logs: `GET /api/v1/admin/ops/rate-limit-events`
5. Notify team and document in privacy incident system

## Rollback Procedure
```bash
# 1. Identify last working release
curl http://localhost:8000/api/v1/admin/ops/releases

# 2. Mark current as rolled back
curl -X POST http://localhost:8000/api/v1/admin/ops/releases/<id>/mark-rollback

# 3. Stop and redeploy with previous image
docker compose -f docker-compose.prod.yml down
docker pull buscamedicos-backend:<previous_tag>
docker compose -f docker-compose.prod.yml up -d
```
