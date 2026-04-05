# Go-Live Checklist

## Pre-Deployment (1 week before)
- [ ] `.env.production` configured with strong secrets
- [ ] TLS certificates working via Caddy
- [ ] PostgreSQL backup tested
- [ ] Files backup tested
- [ ] Smoke tests passing
- [ ] All migrations applied
- [ ] Seed data loaded
- [ ] Health endpoints responding correctly
- [ ] Rate limiting configured
- [ ] Admin accounts created with `admin_ops` role

## Security Checklist
- [ ] `SECRET_KEY` is unique and strong
- [ ] `POSTGRES_PASSWORD` is strong
- [ ] CORS restricted to production domain
- [ ] Debug mode disabled (`DEBUG=false`)
- [ ] `ALLOWED_ORIGINS` set to production domain
- [ ] Backup retention configured
- [ ] No secrets in `.env.example` or documentation
- [ ] Admin ops role assigned to operations team

## Infrastructure Checklist
- [ ] VPS has sufficient disk space (50GB+ recommended)
- [ ] Domain DNS pointing to VPS
- [ ] Docker and Docker Compose installed
- [ ] PostgreSQL client tools available
- [ ] Backup directory created and writable
- [ ] Log rotation configured
- [ ] Monitoring for disk space

## Functional Checklist
- [ ] User registration works
- [ ] Professional registration works
- [ ] Appointment creation works
- [ ] Payment flow works (sandbox)
- [ ] Teleconsultation metadata works
- [ ] Privacy consent flow works
- [ ] Privacy access control enforced
- [ ] Moderation endpoints accessible
- [ ] All health checks passing

## Post-Deployment
- [ ] Smoke tests passing
- [ ] Release registered in deployment_releases
- [ ] Backup job triggered successfully
- [ ] Restore test completed
- [ ] Monitoring active
- [ ] Team notified of deployment
