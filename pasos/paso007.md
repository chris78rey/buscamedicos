Se deja el **paso 7 masticado** para OpenCode: **privacidad fuerte + acceso clínico excepcional auditado + cumplimiento reforzado de datos sensibles**, alineado con la regla central del proyecto de que los administradores no deben ver datos clínicos salvo acceso excepcional, justificado y auditado. 

```text id="48271"
IMPLEMENTAR PASO 7 DEL MARKETPLACE DE SALUD.

CONTEXTO FIJO
- Stack: Flutter + FastAPI + PostgreSQL + Docker Compose.
- Paso 1 ya existe: auth, roles, verification, agreements, audit.
- Paso 2 ya existe: perfiles públicos, disponibilidades, citas.
- Paso 3 ya existe: pagos y comisión.
- Paso 4 ya existe: teleconsulta básica, nota clínica simple, receta, indicaciones.
- Paso 5 ya existe: órdenes de examen, laboratorios y resultados.
- Paso 6 ya existe: reviews, reportes, moderación, sanciones.
- No cambiar arquitectura.
- Mantener soft delete, auditoría, versionado, estados y reversibilidad.
- La plataforma sigue siendo intermediario tecnológico.
- Regla central: admin NO puede ver datos clínicos por defecto.
- Cualquier acceso clínico excepcional debe ser:
  1) solicitado
  2) justificado
  3) aprobado
  4) limitado en tiempo
  5) auditado
  6) revocable
  7) visible en trazabilidad

OBJETIVO
Implementar:
1. clasificación formal de datos y recursos sensibles
2. políticas de acceso contextual a datos clínicos
3. acceso clínico excepcional auditado
4. consentimiento/autorización del paciente para acceso extraordinario cuando aplique
5. bitácora reforzada de accesos clínicos
6. inventario de tratamientos de datos
7. retención lógica y borrado seguro no destructivo
8. exportación de auditoría y trazabilidad
9. pantallas Flutter mínimas para privacidad/seguridad

NO IMPLEMENTAR
- cifrado KMS externo complejo
- anonimización avanzada masiva
- portal legal completo para autoridad externa
- firma electrónica avanzada para cada acceso
- DLP empresarial complejo
- SIEM externo
- consentimiento biométrico
- motor de políticas ABAC distribuido
- cumplimiento documental legal externo completo
- gestión de cookies pública compleja

ENFOQUE
Implementar una capa sólida y reutilizable:
- clasificación del recurso
- decisión de acceso por rol + relación + contexto + sensibilidad
- acceso excepcional como flujo formal separado
- auditoría reforzada de lectura y descarga
- evidencia de justificación y aprobación
- expiración automática del acceso
- exportación administrativa de trazabilidad sin exponer clínico masivamente

ROLES NUEVOS
Agregar:
- admin_privacy
- privacy_auditor

REGLAS DE ROLES
- admin_privacy puede gestionar solicitudes de acceso excepcional, parámetros de privacidad, retención y exportes de auditoría
- privacy_auditor puede revisar trazabilidad y reportes de acceso, sin operar clínicamente
- ninguno tiene acceso clínico libre por defecto
- super_admin tampoco tiene acceso clínico libre
- solo con exceptional access aprobado y vigente podrán leer el recurso específico permitido

CONCEPTOS BASE
Definir niveles de sensibilidad:
- public
- internal
- personal
- sensitive_health
- restricted_legal

Definir tipos de recurso:
- clinical_note
- prescription
- care_instruction
- clinical_file
- teleconsultation_meta
- exam_order
- exam_result
- exam_result_file
- appointment_meta
- audit_export
- consent_record

REGLAS DE NEGOCIO
1. Todo recurso clínico debe tener clasificación.
2. Todo endpoint clínico debe resolver decisión con motor de acceso contextual.
3. El acceso normal permitido se basa en:
   - rol
   - relación asistencial
   - propiedad del recurso
   - estado del recurso
   - sanciones activas
4. El acceso excepcional jamás es global; debe ser por recurso o alcance delimitado.
5. Toda solicitud excepcional requiere motivo.
6. Toda aprobación excepcional requiere aprobador identificado.
7. Cuando aplique, debe existir autorización del paciente o base operacional documentada.
8. Todo acceso excepcional tiene expiración.
9. Todo acceso excepcional es revocable antes de expirar.
10. Toda lectura clínica sensible deja auditoría reforzada.
11. Toda descarga de archivo sensible deja auditoría reforzada.
12. Ningún admin debe poder listar masivamente recursos clínicos solo por tener rol administrativo.
13. Las búsquedas y listados clínicos deben estar limitados por relación válida o acceso excepcional.
14. El sistema debe permitir exportar la trazabilidad de accesos, no el contenido clínico masivo.
15. No borrar físicamente auditorías ni consentimientos críticos.
16. Toda actualización de política o parámetro de privacidad debe quedar auditada y versionada.
17. Debe existir base para responder a solicitudes internas de revisión de acceso.
18. Debe existir base para marcar tratamiento de datos sensibles por módulo.
19. Debe existir retención lógica configurable por tipo de recurso.
20. Debe existir política de minimización de datos en respuestas API administrativas.

TABLAS NUEVAS

1) data_classifications
- id uuid pk
- code varchar unique not null            # public, internal, personal, sensitive_health, restricted_legal
- name varchar not null
- description text null
- severity_level int not null
- is_active boolean default true
- created_at
- updated_at
- deleted_at null
- version int default 1

2) resource_access_policies
- id uuid pk
- resource_type varchar not null
- classification_code varchar not null
- access_mode varchar not null            # normal, exceptional_only, hybrid
- requires_relationship boolean default true
- requires_patient_authorization boolean default false
- requires_justification boolean default false
- max_access_minutes int null
- allow_download boolean default false
- is_active boolean default true
- created_at
- updated_at
- deleted_at null
- version int default 1
- unique(resource_type)

3) patient_privacy_consents
- id uuid pk
- patient_id fk not null
- consent_type varchar not null           # data_processing_health, exceptional_clinical_access, data_export, teleconsultation, lab_result_sharing
- status varchar not null                 # granted, revoked, expired
- granted_at timestamptz not null
- revoked_at timestamptz null
- expires_at timestamptz null
- source varchar not null                 # clickwrap, signed_file, recorded_confirmation, admin_documented_basis
- evidence_file_id fk null
- granted_by_user_id fk null
- notes text null
- created_at
- updated_at
- deleted_at null
- version int default 1

4) exceptional_access_requests
- id uuid pk
- requester_user_id fk not null
- requester_role_code varchar not null
- patient_id fk null
- target_user_id fk null
- resource_type varchar not null
- resource_id uuid null
- scope_type varchar not null             # single_resource, appointment_scope, patient_scope_limited
- justification text not null
- business_basis varchar null
- requested_minutes int not null
- status varchar not null                 # requested, pending_patient_authorization, approved, rejected, expired, revoked, consumed
- requires_patient_authorization boolean default false
- patient_consent_id fk null
- approved_by_user_id fk null
- approved_at timestamptz null
- rejected_by_user_id fk null
- rejected_at timestamptz null
- rejection_reason text null
- starts_at timestamptz null
- expires_at timestamptz null
- revoked_by_user_id fk null
- revoked_at timestamptz null
- revoke_reason text null
- created_at
- updated_at
- deleted_at null
- version int default 1

5) exceptional_access_grants
- id uuid pk
- request_id fk unique not null
- grantee_user_id fk not null
- resource_type varchar not null
- resource_id uuid null
- scope_type varchar not null
- granted_at timestamptz not null
- expires_at timestamptz not null
- status varchar not null                 # active, expired, revoked, consumed
- created_at
- updated_at
- deleted_at null
- version int default 1

6) clinical_access_logs
- id uuid pk
- actor_user_id fk not null
- actor_role_code varchar not null
- patient_id fk null
- target_user_id fk null
- resource_type varchar not null
- resource_id uuid null
- access_mode varchar not null            # normal, exceptional
- action varchar not null                 # read, list, download, export_meta
- decision varchar not null               # allowed, denied
- policy_snapshot_json jsonb null
- exceptional_access_request_id fk null
- justification text null
- ip_address varchar null
- user_agent text null
- request_id varchar null
- created_at

7) processing_activities
- id uuid pk
- code varchar unique not null
- module_name varchar not null
- purpose text not null
- data_categories_json jsonb not null
- subject_categories_json jsonb not null
- legal_basis text null
- retention_policy_id fk null
- is_sensitive boolean default true
- is_active boolean default true
- created_at
- updated_at
- deleted_at null
- version int default 1

8) retention_policies
- id uuid pk
- code varchar unique not null
- resource_type varchar not null
- retention_days int null
- archive_after_days int null
- delete_mode varchar not null            # soft_only, soft_then_archive
- description text null
- is_active boolean default true
- created_at
- updated_at
- deleted_at null
- version int default 1

9) privacy_incidents
- id uuid pk
- incident_code varchar unique not null
- detected_at timestamptz not null
- reported_by_user_id fk null
- severity varchar not null               # low, medium, high, critical
- incident_type varchar not null          # unauthorized_access, overexposure, policy_violation, export_violation, other
- description text not null
- affected_resource_type varchar null
- affected_resource_id uuid null
- status varchar not null                 # open, under_review, contained, resolved, dismissed
- assigned_admin_id fk null
- resolution_summary text null
- resolved_at timestamptz null
- created_at
- updated_at
- deleted_at null
- version int default 1

10) privacy_incident_events
- id uuid pk
- privacy_incident_id fk not null
- event_type varchar not null             # opened, assigned, contained, note_added, resolved, dismissed
- event_payload_json jsonb null
- created_by_user_id fk not null
- created_at

11) privacy_policy_versions
- id uuid pk
- policy_type varchar not null            # patient_privacy, professional_privacy, internal_access_policy, retention_policy
- version_code varchar not null
- content_markdown text not null
- is_active boolean default false
- published_at timestamptz null
- created_at
- updated_at
- deleted_at null
- version int default 1
- unique(policy_type, version_code)

12) privacy_policy_acceptances
- id uuid pk
- policy_version_id fk not null
- user_id fk not null
- accepted_at timestamptz not null
- ip_address varchar null
- user_agent text null
- status varchar not null                 # accepted, superseded
- created_at
- updated_at
- deleted_at null
- version int default 1

CAMBIOS A TABLAS EXISTENTES

files
agregar:
- classification_code varchar null
- retention_policy_id fk null
- legal_hold boolean default false

clinical_files / exam_result_files / otros recursos sensibles
- deben guardar classification_code = sensitive_health si aplica

audit_events
- permitir flag boolean:
  - contains_sensitive_meta boolean default false

MÁQUINAS DE ESTADO

patient_privacy_consents.status
- granted
- revoked
- expired

Transiciones:
- granted -> revoked
- granted -> expired

exceptional_access_requests.status
- requested
- pending_patient_authorization
- approved
- rejected
- expired
- revoked
- consumed

Transiciones:
- requested -> pending_patient_authorization
- requested -> approved
- requested -> rejected
- pending_patient_authorization -> approved
- pending_patient_authorization -> rejected
- approved -> consumed
- approved -> expired
- approved -> revoked

exceptional_access_grants.status
- active
- expired
- revoked
- consumed

Transiciones:
- active -> consumed
- active -> expired
- active -> revoked

privacy_incidents.status
- open
- under_review
- contained
- resolved
- dismissed

Transiciones:
- open -> under_review
- under_review -> contained
- under_review -> resolved
- under_review -> dismissed
- contained -> resolved

REGLAS DE ACCESO NORMAL
1. patient puede leer sus propios recursos clínicos autorizados.
2. professional puede leer recursos clínicos de su relación asistencial válida.
3. laboratory solo accede a datos mínimos de órdenes/resultados asignados.
4. admin no puede leer clínico por acceso normal.
5. privacy_auditor puede ver logs y metadatos, no contenido clínico.
6. admin_privacy puede gestionar solicitudes y políticas, no contenido clínico libre.

REGLAS DE ACCESO EXCEPCIONAL
1. El acceso excepcional solo aplica a recursos sensibles.
2. Debe existir solicitud formal.
3. Debe existir aprobación de admin_privacy o autoridad interna equivalente.
4. Si la política del recurso lo exige, debe existir consentimiento/autorización del paciente o base documentada.
5. El grant debe tener tiempo máximo.
6. El grant solo permite acción delimitada y recurso delimitado.
7. El grant puede consumirse una sola vez si así se define para recursos ultra sensibles.
Implementación simple:
- scope_type puede ser:
  - single_resource
  - appointment_scope
  - patient_scope_limited
- max_access_minutes se toma de resource_access_policies

REGLAS DE MINIMIZACIÓN
1. Endpoints admin nunca devuelven contenido clínico completo salvo exceptional grant válido.
2. Exportes de auditoría solo incluyen metadatos:
   - quién
   - cuándo
   - qué recurso
   - decisión
   - modalidad de acceso
3. No exponer private_professional_note en exportes administrativos.
4. No exponer result_data_json completo en listados administrativos.
5. No exponer archivos sensibles por URL directa sin control de autorización.

REGLAS DE RETENCIÓN
1. Los recursos críticos usan soft delete.
2. Si una retention policy dice archive_after_days, solo marcar elegible; no borrar físico en este paso.
3. legal_hold bloquea archivo lógico/archivado.
4. Auditorías y consentimientos críticos no se eliminan.
5. Debe existir endpoint/meta para consultar la política aplicable a un recurso.

SERVICIOS
1. resource classification service
2. contextual access decision service
3. exceptional access request service
4. exceptional access grant service
5. patient consent service
6. privacy policy service
7. clinical access logging service
8. retention policy service
9. privacy incident service
10. audit export service

FUNCIÓN CENTRAL
Implementar helper reusable:
evaluate_sensitive_access(
    actor_user,
    resource_type,
    resource_id,
    action,
    context
) -> {
    allowed: bool,
    mode: normal|exceptional,
    decision_reason: str,
    policy_snapshot: dict,
    requires_exceptional_request: bool
}

Debe ser usado por:
- clinical note
- prescription
- care instructions
- clinical files
- exam results
- exam result files
- teleconsultation meta sensible

ENDPOINTS NUEVOS

PATIENT
- GET /api/v1/patient/privacy/consents
- POST /api/v1/patient/privacy/consents
- POST /api/v1/patient/privacy/consents/{id}/revoke
- GET /api/v1/patient/privacy/policies/active
- GET /api/v1/patient/privacy/access-log/me

PROFESSIONAL
- POST /api/v1/professionals/me/privacy/exceptional-access-requests
- GET /api/v1/professionals/me/privacy/exceptional-access-requests
- GET /api/v1/professionals/me/privacy/access-log/me

LABORATORY
- POST /api/v1/laboratories/me/privacy/exceptional-access-requests
- GET /api/v1/laboratories/me/privacy/exceptional-access-requests

ADMIN PRIVACY
- GET /api/v1/admin/privacy/policies
- POST /api/v1/admin/privacy/policies
- POST /api/v1/admin/privacy/policies/{id}/publish

- GET /api/v1/admin/privacy/resource-policies
- PUT /api/v1/admin/privacy/resource-policies/{resource_type}

- GET /api/v1/admin/privacy/exceptional-access-requests
- GET /api/v1/admin/privacy/exceptional-access-requests/{id}
- POST /api/v1/admin/privacy/exceptional-access-requests/{id}/approve
- POST /api/v1/admin/privacy/exceptional-access-requests/{id}/reject
- POST /api/v1/admin/privacy/exceptional-access-requests/{id}/revoke

- GET /api/v1/admin/privacy/access-logs
- GET /api/v1/admin/privacy/access-logs/export-meta

- GET /api/v1/admin/privacy/processing-activities
- POST /api/v1/admin/privacy/processing-activities
- PUT /api/v1/admin/privacy/processing-activities/{id}

- GET /api/v1/admin/privacy/retention-policies
- POST /api/v1/admin/privacy/retention-policies
- PUT /api/v1/admin/privacy/retention-policies/{id}

- GET /api/v1/admin/privacy/incidents
- GET /api/v1/admin/privacy/incidents/{id}
- POST /api/v1/admin/privacy/incidents
- POST /api/v1/admin/privacy/incidents/{id}/assign
- POST /api/v1/admin/privacy/incidents/{id}/contain
- POST /api/v1/admin/privacy/incidents/{id}/resolve
- POST /api/v1/admin/privacy/incidents/{id}/dismiss

PRIVACY AUDITOR
- GET /api/v1/privacy-auditor/access-logs
- GET /api/v1/privacy-auditor/access-logs/{id}
- GET /api/v1/privacy-auditor/incidents
- GET /api/v1/privacy-auditor/processing-activities

REQUEST/RESPONSE CLAVES

POST /patient/privacy/consents
input:
- consent_type
- source
- evidence_file_id optional
- expires_at optional
- notes optional
output:
- consent_id
- status
- granted_at

POST /professionals/me/privacy/exceptional-access-requests
input:
- patient_id optional
- target_user_id optional
- resource_type
- resource_id optional
- scope_type
- justification
- business_basis optional
- requested_minutes
output:
- request_id
- status
- requires_patient_authorization

POST /admin/privacy/exceptional-access-requests/{id}/approve
input:
- starts_at optional
- expires_at
- approval_note optional
output:
- request_id
- status
- grant_id
- granted_until

GET /admin/privacy/access-logs/export-meta
filters:
- actor_user_id optional
- resource_type optional
- from optional
- to optional
output:
- export generated with metadata only
No incluir contenido clínico.

PUT /admin/privacy/resource-policies/{resource_type}
input:
- classification_code
- access_mode
- requires_relationship
- requires_patient_authorization
- requires_justification
- max_access_minutes
- allow_download
output:
- resource_type
- version
- is_active

VALIDACIONES
1. consent_type válido.
2. exceptional access request debe tener justification.
3. requested_minutes > 0.
4. approve requiere expires_at futuro.
5. no aprobar request ya resuelta.
6. no usar grant expirado.
7. no usar grant revocado.
8. si policy requiere patient authorization, no aprobar sin consent válido o base documentada explícita.
9. acceso clínico denegado debe igual registrar clinical_access_logs con decision=denied.
10. export_meta nunca puede incluir contenido clínico.
11. privacy_auditor no puede cambiar políticas.
12. admin_privacy no puede saltarse el motor de acceso leyendo recurso clínico por endpoint alterno.
13. retention policy no puede aplicarse si legal_hold = true.
14. publicar nueva privacy policy debe dejar anterior activa como superseded donde corresponda.

AUDITORÍA OBLIGATORIA
Registrar audit_event en:
- crear/revocar consent
- crear/aprobar/rechazar/revocar exceptional access request
- cambiar resource access policy
- crear/editar retention policy
- crear/editar processing activity
- crear/contener/resolver privacy incident
- exportar logs
Registrar clinical_access_logs en:
- toda lectura/listado/descarga de recurso sensible
- decisiones allowed o denied
- modo normal o exceptional

PANTALLAS FLUTTER MÍNIMAS

PATIENT
1. ver consentimientos activos
2. otorgar/revocar consentimientos simples
3. ver políticas activas
4. ver su trazabilidad de accesos relacionados

PROFESSIONAL
1. crear solicitud de acceso excepcional
2. ver estado de solicitudes propias
3. ver trazabilidad propia de accesos excepcionales

LABORATORY
1. crear solicitud de acceso excepcional
2. ver estado de solicitudes propias

ADMIN PRIVACY
1. listado de solicitudes excepcionales
2. detalle y aprobación/rechazo
3. listado de access logs
4. export meta de trazabilidad
5. gestión básica de políticas de recurso
6. gestión básica de retention policies
7. listado de incidentes de privacidad
8. contención y resolución

PRIVACY AUDITOR
1. vista de logs
2. vista de incidentes
3. vista de processing activities
4. sin acceso al contenido clínico

NO HACER UI COMPLEJA
- diseño simple
- loading/error/empty
- cliente HTTP limpio
- sin optimización prematura

SEEDS
- data_classifications:
  - public
  - internal
  - personal
  - sensitive_health
  - restricted_legal

- resource_access_policies iniciales:
  clinical_note -> sensitive_health, exceptional_only, requires_relationship=true, requires_patient_authorization=true, requires_justification=true, allow_download=false
  prescription -> sensitive_health, hybrid, requires_relationship=true, requires_patient_authorization=false, requires_justification=false, allow_download=true
  care_instruction -> sensitive_health, hybrid, requires_relationship=true, allow_download=true
  clinical_file -> sensitive_health, exceptional_only, requires_relationship=true, requires_patient_authorization=true, allow_download=false
  exam_result -> sensitive_health, hybrid, requires_relationship=true, allow_download=true
  exam_result_file -> sensitive_health, hybrid, requires_relationship=true, allow_download=true
  teleconsultation_meta -> personal, hybrid
  appointment_meta -> internal, normal

- feature_flag privacy_hardening_enabled=true
- feature_flag exceptional_access_enabled=true
- feature_flag retention_policies_enabled=true
- feature_flag privacy_incidents_enabled=true

ORDEN EXACTO DE IMPLEMENTACIÓN
1. migraciones
2. seeds
3. modelos ORM
4. schemas
5. contextual access decision service
6. consent service
7. exceptional access request/grant service
8. clinical access logging service
9. privacy policy service
10. retention policy service
11. privacy incident service
12. endpoints
13. tests backend
14. pantallas Flutter
15. integración Flutter-API
16. README paso 7

PRUEBAS AUTOMÁTICAS
1. admin sin grant no puede leer clinical_note
2. professional con relación válida sí puede según policy
3. denied access genera clinical_access_log
4. exceptional access request se crea con justification
5. request no se aprueba sin patient consent cuando policy lo exige
6. request aprobado crea grant con expiración
7. grant expirado ya no permite acceso
8. grant revocado bloquea acceso
9. patient puede revocar consent
10. export_meta no incluye contenido clínico
11. privacy_auditor ve logs pero no contenido clínico
12. retention policy no actúa si legal_hold=true
13. cambio de resource policy queda auditado
14. privacy incident puede abrirse y resolverse
15. access_mode normal vs exceptional queda bien registrado

CRITERIOS DE ACEPTACIÓN
- el acceso clínico sensible queda gobernado por policy reusable
- admin no ve clínico por defecto
- acceso excepcional existe como flujo formal
- grants expiran y pueden revocarse
- toda lectura clínica sensible queda trazada
- exportes administrativos solo muestran metadatos
- consentimientos y políticas quedan versionados
- incidentes de privacidad pueden registrarse y resolverse
- tests pasan

SALIDA ESPERADA
Entregar directamente:
- migraciones
- modelos
- servicios
- endpoints
- tests
- pantallas Flutter mínimas
- README breve

NO EXPLICAR DEMASIADO.
IMPLEMENTAR.
```

Versión más corta para consumir menos tokens:

```text id="15384"
Implementar paso 7:
privacidad fuerte + acceso clínico excepcional auditado + retención + trazabilidad.

Base existente:
FastAPI + PostgreSQL + Flutter.
Pasos 1 a 6 ya existen.

No implementar:
KMS externo, SIEM, anonimización masiva, firma avanzada por acceso, DLP complejo.

Agregar roles:
- admin_privacy
- privacy_auditor

Crear tablas:
data_classifications
resource_access_policies
patient_privacy_consents
exceptional_access_requests
exceptional_access_grants
clinical_access_logs
processing_activities
retention_policies
privacy_incidents
privacy_incident_events
privacy_policy_versions
privacy_policy_acceptances

Cambios:
files.classification_code
files.retention_policy_id
files.legal_hold

Reglas:
- todo recurso clínico tiene clasificación
- access decision = rol + relación + contexto + policy
- admin no ve clínico por defecto
- acceso excepcional requiere solicitud, justificación, aprobación, expiración y auditoría
- si policy lo exige, requiere consentimiento/autorización del paciente
- toda lectura/descarga sensible deja log allowed o denied
- exportes admin solo metadatos, no contenido clínico
- soft delete y legal_hold

Implementar helper:
evaluate_sensitive_access(actor, resource_type, resource_id, action, context)

Endpoints:
GET /patient/privacy/consents
POST /patient/privacy/consents
POST /patient/privacy/consents/{id}/revoke
GET /patient/privacy/policies/active
GET /patient/privacy/access-log/me

POST /professionals/me/privacy/exceptional-access-requests
GET /professionals/me/privacy/exceptional-access-requests
GET /professionals/me/privacy/access-log/me

POST /laboratories/me/privacy/exceptional-access-requests
GET /laboratories/me/privacy/exceptional-access-requests

GET /admin/privacy/policies
POST /admin/privacy/policies
POST /admin/privacy/policies/{id}/publish
GET /admin/privacy/resource-policies
PUT /admin/privacy/resource-policies/{resource_type}
GET /admin/privacy/exceptional-access-requests
GET /admin/privacy/exceptional-access-requests/{id}
POST /admin/privacy/exceptional-access-requests/{id}/approve
POST /admin/privacy/exceptional-access-requests/{id}/reject
POST /admin/privacy/exceptional-access-requests/{id}/revoke
GET /admin/privacy/access-logs
GET /admin/privacy/access-logs/export-meta
CRUD básico processing_activities
CRUD básico retention_policies
CRUD básico privacy_incidents

GET /privacy-auditor/access-logs
GET /privacy-auditor/incidents
GET /privacy-auditor/processing-activities

Tests:
- admin sin grant no accede
- denied genera log
- request requiere justification
- policy con patient authorization no aprueba sin consent
- grant expira
- grant revocado bloquea
- export_meta sin clínico
- privacy_auditor sin clínico
- legal_hold bloquea retención
- incidentes funcionan

Entregar código, migraciones, tests, Flutter mínimo y README.
```

Luego correspondería el **paso 8**: **endurecimiento final para salida real, observabilidad, backups, despliegue VPS, límites, recuperación y pruebas E2E**.
