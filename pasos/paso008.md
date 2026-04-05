Se deja el **paso 8 masticado** para OpenCode: **endurecimiento final para salida real + observabilidad + backups + despliegue VPS + límites + recuperación + pruebas E2E**, como cierre operativo antes de publicar una primera versión seria. Este paso no agrega negocio nuevo; vuelve confiable, auditable y operable lo ya construido. 

```text id="42716"
IMPLEMENTAR PASO 8 DEL MARKETPLACE DE SALUD.

CONTEXTO FIJO
- Stack: Flutter + FastAPI + PostgreSQL + Docker Compose.
- Pasos 1 a 7 ya existen.
- No cambiar arquitectura base.
- Mantener soft delete, auditoría, versionado, estados y reversibilidad.
- Admin NO puede ver datos clínicos por defecto.
- La plataforma sigue siendo intermediario tecnológico.
- Este paso es de endurecimiento operativo y salida real a VPS.

OBJETIVO
Implementar:
1. despliegue productivo en VPS con Docker Compose
2. perfiles por ambiente: local, staging, production
3. reverse proxy y TLS
4. healthchecks, readiness y liveness
5. logs estructurados y correlación por request_id
6. métricas y observabilidad básica
7. rate limiting y protecciones base
8. backups automáticos y verificación de restauración
9. rotación de logs y housekeeping
10. manejo seguro de secretos y variables
11. tareas programadas mínimas
12. pruebas E2E y smoke tests
13. runbooks operativos
14. controles de recursos para bajo consumo RAM
15. mecanismo de rollback operativo
16. validaciones previas a go-live

NO IMPLEMENTAR
- Kubernetes
- microservicios
- SIEM empresarial externo
- autoscaling complejo
- multi-VPS
- DR geográfico avanzado
- CDN compleja
- blue/green sofisticado
- caos engineering
- terraform obligatorio
- SSO empresarial
- WAF complejo de proveedor externo
- observabilidad de nivel enterprise con alto costo

ENFOQUE
Mantener despliegue simple, austero y confiable:
- un solo VPS
- Docker Compose con perfiles
- reverse proxy
- API FastAPI
- PostgreSQL
- Redis opcional si ya existe por pasos previos
- almacenamiento local estructurado
- backups externos o en directorio montado
- monitoreo simple pero suficiente
- restauración comprobable

REGLAS DE NEGOCIO Y OPERACIÓN
1. Ninguna mejora operativa debe romper trazabilidad previa.
2. Ningún proceso de mantenimiento debe borrar físicamente datos críticos.
3. Toda tarea automática crítica debe dejar log.
4. Toda exportación o backup crítico debe ser auditable.
5. Todo servicio productivo debe tener healthcheck.
6. El sistema debe seguir funcionando con recursos modestos de VPS.
7. Debe existir capacidad de recuperación razonable ante caída de contenedor.
8. El rollback debe ser por imagen/version/tag, no por cambios manuales improvisados.
9. La salida real exige verificación de backups restaurables.
10. No exponer PostgreSQL al exterior.
11. No exponer Redis al exterior.
12. Los archivos sensibles no deben servirse por rutas públicas sin control de autorización.
13. Deben existir límites básicos contra abuso de login, API y subida de archivos.
14. Deben existir logs suficientes para reconstruir incidentes operativos.
15. Debe existir checklist de despliegue y checklist de incidente.

COMPONENTES OPERATIVOS A IMPLEMENTAR

1) reverse proxy
Elegir uno y dejarlo fijo:
- caddy o traefik o nginx
Recomendación simple:
- caddy para menor complejidad
Debe hacer:
- TLS
- proxy a backend
- servir Flutter web build
- headers de seguridad base
- compresión si aplica
- límites básicos de upload configurables

2) docker compose production
Crear:
- docker-compose.yml base
- docker-compose.override.yml para local si ya existe
- docker-compose.prod.yml
- .env.example
- .env.production.example

Servicios mínimos producción:
- reverse_proxy
- backend_api
- postgres
- redis opcional por perfil
- backup_runner
- cron_runner opcional o scheduler interno si ya existe
- no agregar servicios innecesarios

3) imágenes y versionado
- Dockerfiles multi-stage
- tags versionadas
- healthcheck por imagen
- usuario no root cuando sea viable
- nada de latest
- build reproducible

4) observabilidad mínima
- logs JSON en backend
- request_id en todas las respuestas y logs
- métricas HTTP básicas
- endpoint /health/live
- endpoint /health/ready
- endpoint /metrics si se implementa simple
- dashboard opcional simple si no aumenta mucho RAM
- tabla o archivo de eventos operativos si aporta trazabilidad

5) seguridad operativa
- rate limiting por IP y usuario
- login throttling
- headers seguros
- CORS estricto por ambiente
- trusted hosts
- tamaño máximo de payload configurable
- tamaño máximo de archivo configurable
- sanitización de logs para no filtrar clínico
- rotación de tokens/secretos por .env
- cookies seguras si aplican
- forzar HTTPS en producción

6) backups y restauración
Implementar backups para:
- PostgreSQL
- archivos subidos
- configuración crítica no secreta
Estrategia mínima:
- pg_dump diario
- backup incremental/simple de storage por fecha
- hashes o manifest opcional para archivos
- retención configurable
- script de restore documentado
- prueba de restore en entorno temporal

7) housekeeping
- limpieza de temporales
- expiración de grants vencidos
- expiración de solicitudes vencidas
- expiración de tokens o sesiones según modelo existente
- rotación de logs
- marcado de sanciones expiradas
- marcado de access grants expirados
- tareas periódicas con logs

8) pruebas finales
- smoke tests post deploy
- E2E mínimos de flujos críticos
- verificación de migraciones
- verificación de permisos
- verificación de acceso clínico restringido
- verificación de backup/restore

TABLAS NUEVAS

1) deployment_releases
- id uuid pk
- release_code varchar unique not null
- git_commit varchar null
- image_tag varchar not null
- environment varchar not null              # local, staging, production
- deployed_by_user_id fk null
- deployed_at timestamptz not null
- status varchar not null                   # deployed, rolled_back, failed
- notes text null
- created_at
- updated_at
- deleted_at null
- version int default 1

2) operational_jobs
- id uuid pk
- job_code varchar unique not null
- job_type varchar not null                 # backup_db, backup_files, cleanup_temp, expire_access, rotate_logs, restore_test
- schedule_cron varchar null
- is_active boolean default true
- last_run_at timestamptz null
- last_status varchar null                  # success, failed, running
- last_duration_ms bigint null
- last_error text null
- created_at
- updated_at
- deleted_at null
- version int default 1

3) operational_job_runs
- id uuid pk
- operational_job_id fk not null
- started_at timestamptz not null
- finished_at timestamptz null
- status varchar not null                   # running, success, failed
- output_summary text null
- metadata_json jsonb null
- created_at
- updated_at
- deleted_at null
- version int default 1

4) backup_artifacts
- id uuid pk
- backup_type varchar not null              # postgres_dump, files_archive, restore_test_report
- artifact_path text not null
- artifact_hash varchar null
- size_bytes bigint null
- started_at timestamptz not null
- finished_at timestamptz null
- status varchar not null                   # started, success, failed, verified
- retention_until timestamptz null
- verification_notes text null
- created_at
- updated_at
- deleted_at null
- version int default 1

5) system_health_snapshots
- id uuid pk
- environment varchar not null
- service_name varchar not null
- health_status varchar not null            # healthy, degraded, unhealthy
- details_json jsonb null
- captured_at timestamptz not null
- created_at
- updated_at
- deleted_at null
- version int default 1

6) rate_limit_events
- id uuid pk
- actor_user_id fk null
- ip_address varchar null
- route_key varchar not null
- event_type varchar not null               # throttle, block, cooldown
- created_at
- updated_at
- deleted_at null
- version int default 1

CAMBIOS A TABLAS EXISTENTES
audit_events
agregar opcional:
- operational_scope boolean default false
- release_code varchar null

system_parameters
usar para:
- backup retention
- max upload size
- request limits
- allowed origins
- job schedules
- environment flags

FEATURE FLAGS NUEVAS
- go_live_guard_enabled
- production_observability_enabled
- automated_backups_enabled
- restore_test_enabled
- rate_limit_enabled
- e2e_smoke_enabled

RUTAS Y ENDPOINTS NUEVOS

HEALTH / OBSERVABILITY
- GET /health/live
- GET /health/ready
- GET /health/details              # solo admin técnico/autorizado
- GET /metrics                     # si se implementa
- GET /version

ADMIN OPS
- GET /api/v1/admin/ops/releases
- POST /api/v1/admin/ops/releases/register
- POST /api/v1/admin/ops/releases/{id}/mark-rollback
- GET /api/v1/admin/ops/jobs
- POST /api/v1/admin/ops/jobs/{job_code}/run
- GET /api/v1/admin/ops/job-runs
- GET /api/v1/admin/ops/backups
- POST /api/v1/admin/ops/backups/run-db
- POST /api/v1/admin/ops/backups/run-files
- POST /api/v1/admin/ops/backups/run-restore-test
- GET /api/v1/admin/ops/health-snapshots
- GET /api/v1/admin/ops/rate-limit-events
- GET /api/v1/admin/ops/config-summary

NOTA
Estos endpoints no deben exponer secretos ni contenido clínico.

REQUEST/RESPONSE CLAVES

POST /api/v1/admin/ops/releases/register
input:
- release_code
- git_commit optional
- image_tag
- environment
- notes optional
output:
- deployment_release_id
- status
- deployed_at

POST /api/v1/admin/ops/backups/run-db
output:
- backup_artifact_id
- status
- started_at

POST /api/v1/admin/ops/backups/run-restore-test
output:
- backup_artifact_id
- status
- verification_notes

GET /health/ready
output:
- app: ready|not_ready
- database: ready|not_ready
- redis: ready|skipped|not_ready
- storage: ready|not_ready
- version
- timestamp

REGLAS DE DESPLIEGUE
1. producción usa .env.production
2. compose prod no expone DB ni Redis al host público
3. reverse proxy expone solo 80/443 o el puerto decidido
4. backend solo expuesto a red interna de compose
5. migraciones deben correr antes del start final o como job explícito controlado
6. release debe quedar registrada en deployment_releases
7. cada despliegue debe tener rollback documentado
8. cada despliegue debe incluir smoke tests automáticos mínimos

REGLAS DE LOGGING
1. logs JSON en backend
2. siempre incluir:
   - timestamp
   - level
   - service
   - request_id
   - user_id si existe
   - route
   - status_code
   - duration_ms
3. nunca loggear:
   - password
   - token completo
   - prescription content completo
   - clinical note completa
   - result_data_json completo
4. errores clínicos deben loggear metadatos mínimos
5. rotación o externalización simple de logs

REGLAS DE RATE LIMIT
Implementar al menos:
- login
- register
- password reset si existe
- create payment intent
- create appointment
- upload file
- report creation
- exceptional access request
Estrategia simple:
- Redis si disponible
- si no, memoria/local limitada para entorno pequeño
Registrar eventos de throttle.

REGLAS DE BACKUP
1. backup DB diario
2. backup de archivos diario o configurable
3. retención configurable
4. manifest simple con fecha, tamaño, hash opcional
5. restore test semanal o bajo demanda
6. restore test debe usar entorno temporal, no producción viva
7. resultado del restore test debe quedar en backup_artifacts y operational_job_runs

REGLAS DE RECUPERACIÓN
1. documentar restore DB
2. documentar restore files
3. documentar reconfiguración post restore
4. documentar rollback de release
5. documentar qué hacer ante:
   - backend caído
   - DB saturada
   - disco lleno
   - TLS vencido
   - backup fallido
   - restore fallido
   - abuso de rate limit
6. todo como runbook en docs/

REGLAS DE PRUEBAS E2E
Implementar E2E mínimos sobre staging o entorno temporal:
1. registro/login patient
2. registro/login professional
3. availability + cita
4. pago sandbox
5. teleconsulta metadata
6. receta o indicación simple
7. orden de examen y liberación de resultado
8. review
9. acceso clínico restringido
10. exceptional access denegado/sin grant
11. health endpoints
12. backup job invocable

Se puede usar:
- pytest + httpx para smoke/backend
- Playwright solo si ya existe y no complica demasiado
- preferencia simple: smoke HTTP + un set pequeño UI

ARCHIVOS A CREAR

infra/
- docker-compose.prod.yml
- .env.production.example
- Caddyfile o config elegida
- scripts/deploy.sh
- scripts/rollback.sh
- scripts/run_migrations.sh
- scripts/backup_db.sh
- scripts/backup_files.sh
- scripts/restore_db.sh
- scripts/restore_files.sh
- scripts/restore_test.sh
- scripts/smoke_test.sh

docs/
- PRODUCTION_DEPLOYMENT.md
- BACKUP_AND_RESTORE.md
- INCIDENT_RUNBOOK.md
- GO_LIVE_CHECKLIST.md
- ROLLBACK_PLAN.md
- OBSERVABILITY.md

SERVICIOS A IMPLEMENTAR
1. health service
2. readiness dependency checker
3. release registry service
4. operational jobs runner
5. backup service
6. restore verification service
7. rate limit service
8. config summary service
9. structured logging config
10. smoke test runner or script integration

VALIDACIONES
1. /health/live no debe depender de DB completa si no hace falta
2. /health/ready sí valida dependencias críticas
3. no exponer secretos en config-summary
4. no permitir run backup o restore test a roles no autorizados
5. no correr restore real sobre producción por endpoint normal
6. no registrar release sin image_tag
7. no marcar rollback sin release válido
8. no ejecutar jobs desactivados salvo override auditado
9. si backup falla, registrar job_run failed y audit_event
10. si disco libre es bajo, marcar health degraded
11. si DB no responde, ready = false
12. si Redis no es obligatorio y no está activo, ready puede ser degraded o skipped según config

AUDITORÍA OBLIGATORIA
Registrar audit_event en:
- registro de release
- rollback marcado
- ejecución manual de job
- backup DB/files
- restore test
- cambio de parámetros operativos
- export de config summary
- incidentes operativos si se modelan
Marcar operational_scope=true cuando aplique.

PANTALLAS FLUTTER MÍNIMAS
No hacer panel complejo. Solo una sección operativa básica para rol autorizado:
1. estado general del sistema
2. releases recientes
3. backups recientes
4. jobs y última ejecución
5. health snapshots
6. acceso a checklist/runbooks enlazados si aplica

NO HACER UI COMPLEJA
- diseño simple
- tablas básicas
- loading/error/empty
- sin tiempo real complejo

SEEDS
- feature_flag go_live_guard_enabled=true
- feature_flag production_observability_enabled=true
- feature_flag automated_backups_enabled=true
- feature_flag restore_test_enabled=true
- feature_flag rate_limit_enabled=true
- operational_jobs base:
  - backup_db_daily
  - backup_files_daily
  - expire_access_grants_hourly
  - cleanup_temp_daily
  - restore_test_weekly

ORDEN EXACTO DE IMPLEMENTACIÓN
1. dockerfiles multi-stage y compose prod
2. reverse proxy config
3. env examples y config segura
4. health/readiness/version endpoints
5. structured logging + request_id hardening
6. rate limiting
7. tablas operativas + migraciones
8. release registry
9. jobs runner
10. backup scripts + backup service
11. restore test scripts + verification
12. config summary seguro
13. smoke tests
14. E2E mínimos
15. docs/runbooks/checklists
16. panel Flutter mínimo ops
17. README paso 8

PRUEBAS AUTOMÁTICAS
1. live endpoint responde
2. ready endpoint refleja DB caída
3. config summary no expone secretos
4. release register funciona
5. rollback mark funciona
6. backup job crea artifact
7. backup failure queda registrado
8. restore test genera verification report
9. rate limit en login funciona
10. rate limit en create appointment funciona
11. audit_event operativo se registra
12. no acceso a endpoints ops sin rol autorizado
13. compose prod levanta healthchecks
14. smoke test principal pasa
15. acceso clínico sigue restringido en producción hardening

CRITERIOS DE ACEPTACIÓN
- existe compose productivo usable
- reverse proxy y TLS configurables
- health/live y health/ready funcionan
- logs estructurados con request_id funcionan
- rate limits básicos operan
- backups DB y files corren
- restore test produce evidencia verificable
- releases quedan registradas
- rollback está documentado y soportado
- smoke tests y E2E mínimos pasan
- runbooks y checklist existen
- no se exponen secretos ni clínico
- tests pasan

SALIDA ESPERADA
Entregar directamente:
- dockerfiles
- docker-compose.prod.yml
- config reverse proxy
- migraciones
- modelos
- servicios
- scripts de backup/restore/deploy/smoke
- endpoints ops
- tests
- panel Flutter mínimo ops
- documentación operativa
- README breve

NO EXPLICAR DEMASIADO.
IMPLEMENTAR.
```

Versión más corta para consumir menos tokens:

```text id="19327"
Implementar paso 8:
hardening final + despliegue VPS + observabilidad + backups + rollback + E2E.

Base existente:
FastAPI + PostgreSQL + Flutter.
Pasos 1 a 7 ya existen.

No implementar:
Kubernetes, microservicios, SIEM complejo, autoscaling, multi-VPS.

Crear tablas:
deployment_releases
operational_jobs
operational_job_runs
backup_artifacts
system_health_snapshots
rate_limit_events

Agregar feature flags:
go_live_guard_enabled
production_observability_enabled
automated_backups_enabled
restore_test_enabled
rate_limit_enabled

Implementar:
- docker-compose.prod.yml
- .env.production.example
- reverse proxy con TLS
- health/live
- health/ready
- version endpoint
- logs JSON con request_id
- rate limit en login/register/appointment/payment/upload/report/access request
- backups DB y files
- restore test verificable
- release registry
- rollback script
- smoke tests
- E2E mínimos
- docs de deploy, backup/restore, incident runbook, go-live checklist

Endpoints:
GET /health/live
GET /health/ready
GET /version
GET /api/v1/admin/ops/releases
POST /api/v1/admin/ops/releases/register
POST /api/v1/admin/ops/releases/{id}/mark-rollback
GET /api/v1/admin/ops/jobs
POST /api/v1/admin/ops/jobs/{job_code}/run
GET /api/v1/admin/ops/job-runs
GET /api/v1/admin/ops/backups
POST /api/v1/admin/ops/backups/run-db
POST /api/v1/admin/ops/backups/run-files
POST /api/v1/admin/ops/backups/run-restore-test
GET /api/v1/admin/ops/health-snapshots
GET /api/v1/admin/ops/rate-limit-events
GET /api/v1/admin/ops/config-summary

Scripts:
deploy.sh
rollback.sh
run_migrations.sh
backup_db.sh
backup_files.sh
restore_db.sh
restore_files.sh
restore_test.sh
smoke_test.sh

Reglas:
- no exponer DB ni Redis al exterior
- no secrets en logs ni config summary
- no latest
- healthchecks obligatorios
- backup y restore auditados
- rollback por release/tag
- live simple, ready con dependencias
- acceso clínico sigue restringido

Tests:
- live y ready
- config summary sin secretos
- release register
- backup artifact
- restore test report
- rate limit
- endpoints ops protegidos
- smoke test principal
- acceso clínico no se rompe

Entregar código, compose prod, scripts, tests, docs, Flutter ops mínimo y README.
```

Con ese paso ya queda cerrada la **ruta principal de 8 pasos**. Luego, como capa opcional, convendría dejar un **paso 9 de IA segura y útil** para búsqueda inteligente, resúmenes operativos y apoyo no clínico.
