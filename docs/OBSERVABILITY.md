# Observability Guide

## Health Endpoints

| Endpoint | Auth | Description |
|---|---|---|
| `GET /health/live` | None | Liveness probe |
| `GET /health/ready` | None | Readiness probe |
| `GET /health/details` | admin_ops | Full system status |
| `GET /version` | None | Service version |

## Structured Logging

All HTTP requests generate JSON logs with:
```json
{
  "timestamp": "2024-01-08T12:00:00",
  "level": "info",
  "service": "buscamedicos-api",
  "request_id": "uuid",
  "user_id": "uuid or null",
  "route": "/api/v1/...",
  "method": "GET",
  "status_code": 200,
  "duration_ms": 45
}
```

Logs are output to container stdout (collect with `docker logs` or log aggregator).

## Sensitive Data Filtering
The following are NEVER logged:
- Passwords or password hashes
- Full authentication tokens
- Prescription content
- Clinical notes
- Full `result_data_json` blobs

## Rate Limiting
In-memory rate limiting is active for:
- `login`: 5 requests/minute
- `register`: 3 requests/minute
- `password_reset`: 3 requests/minute
- `create_appointment`: 20 requests/minute
- `upload_file`: 10 requests/minute
- `report_creation`: 10 requests/minute
- `exceptional_access_request`: 5 requests/minute

Monitor throttle events:
```bash
curl http://localhost:8000/api/v1/admin/ops/rate-limit-events
```

## Deployment Monitoring

### Register Deployment
```bash
curl -X POST http://localhost:8000/api/v1/admin/ops/releases/register \
  -H "Content-Type: application/json" \
  -d '{"release_code": "v1.0.0", "image_tag": "v1.0.0", "environment": "production"}'
```

### View Deployments
```bash
curl http://localhost:8000/api/v1/admin/ops/releases
```

### View Health Snapshots
```bash
curl http://localhost:8000/api/v1/admin/ops/health-snapshots
```

### View Backup Status
```bash
curl http://localhost:8000/api/v1/admin/ops/backups
```

### View Operational Jobs
```bash
curl http://localhost:8000/api/v1/admin/ops/jobs
curl http://localhost:8000/api/v1/admin/ops/job-runs
```

## Docker Monitoring
```bash
# Resource usage
docker stats

# Disk usage
docker system df

# Container health
docker compose -f docker-compose.prod.yml ps

# Full logs
docker compose -f docker-compose.prod.yml logs -f backend_api
```

## Simple Alerting (Cron-based)
Add to crontab for disk space alerts:
```cron
*/5 * * * * df -h | awk '$5 > 80 {system("echo disk_warning | mail admin@example.com")}'
```
