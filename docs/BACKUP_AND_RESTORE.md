# Backup and Restore Guide

## Backup Strategy

### Database Backup (Daily via cron)
```cron
0 2 * * * cd /opt/buscamedicos/infra && ./scripts/backup_db.sh
```

### Files Backup (Daily via cron)
```cron
0 3 * * * cd /opt/buscamedicos/infra && ./scripts/backup_files.sh
```

### Restore Test (Weekly via cron)
```cron
0 6 * * 0 cd /opt/buscamedicos/infra && ./scripts/restore_test.sh $(ls -t ../backups/pg_dump_*.dump | head -1)
```

## Backup Location
All backups are stored in `../backups/` relative to the infra directory.

Files:
- `pg_dump_YYYYMMDD_HHMMSS.dump` — PostgreSQL custom format dump
- `files_archive_YYYYMMDD_HHMMSS.tar.gz` — Compressed files archive

## Restore Procedures

### Restore Database
**WARNING: This overwrites the production database. Use only in emergencies.**

```bash
# 1. Stop the backend to prevent writes
docker compose -f docker-compose.prod.yml stop backend_api

# 2. Restore (requires pg_restore)
pg_restore -h localhost -U buscamedicos -d buscamedicos ../backups/pg_dump_YYYYMMDD_HHMMSS.dump --clean --if-exists

# 3. Restart backend
docker compose -f docker-compose.prod.yml start backend_api
```

### Restore Files
```bash
tar xzf ../backups/files_archive_YYYYMMDD_HHMMSS.tar.gz -C /opt/buscamedicos/
```

### Verify Restore
```bash
./scripts/restore_test.sh ../backups/pg_dump_YYYYMMDD_HHMMSS.dump
```

## Retention
- Database dumps: Keep last 30 days
- File archives: Keep last 14 days
- Automated cleanup via operational jobs

## Offsite Backup (Recommended)
Copy backups to external storage daily:
```bash
rsync -avz ../backups/ user@backup-server:/path/to/buscamedicos/backups/
```
