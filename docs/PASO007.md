# Paso 7 - Privacidad y Acceso Clinico Excepcional

## Resumen

Implementa capa de privacidad fuerte + acceso clinico excepcional auditado + cumplimiento reforzado de datos sensibles.

**Regla central**: admin NO puede ver datos clinicos por defecto. Cualquier acceso clinico excepcional debe ser solicitado, justificado, aprobado, limitado en tiempo, auditado y revocable.

## Tablas Nuevas (12 + 3 columnas)

| Tabla | Descripcion |
|---|---|
| `data_classifications` | Codigos de clasificacion: public, internal, personal, sensitive_health, restricted_legal |
| `resource_access_policies` | Politicas de acceso por tipo de recurso |
| `patient_privacy_consents` | Consentimientos de pacientes |
| `exceptional_access_requests` | Solicitudes de acceso excepcional |
| `exceptional_access_grants` | Concesiones de acceso excepcional |
| `clinical_access_logs` | Bitacora de accesos clinicos |
| `processing_activities` | Inventario de tratamientos de datos |
| `retention_policies` | Politicas de retencion de datos |
| `privacy_incidents` | Incidentes de privacidad |
| `privacy_incident_events` | Eventos de incidentes |
| `privacy_policy_versions` | Versiones de politicas de privacidad |
| `privacy_policy_acceptances` | Aceptaciones de politicas |

**Cambios a tablas existentes**:
- `files`: columnas `classification_code`, `retention_policy_id`, `legal_hold`

## Modelos ORM

- `DataClassification`, `ResourceAccessPolicy`
- `PatientPrivacyConsent`, `ExceptionalAccessRequest`, `ExceptionalAccessGrant`
- `ClinicalAccessLog`
- `ProcessingActivity`, `RetentionPolicy`
- `PrivacyIncident`, `PrivacyIncidentEvent`
- `PrivacyPolicyVersion`, `PrivacyPolicyAcceptance`

## Servicios (9)

1. **ResourceClassificationService** - clasificacion de recursos
2. **ContextualAccessDecisionService** - motor de decision de acceso
3. **PatientConsentService** - gestion de consentimientos
4. **ExceptionalAccessRequestService** - solicitudes y concesiones
5. **ClinicalAccessLoggingService** - bitacora de accesos clinicos
6. **PrivacyPolicyService** - politicas de privacidad versionadas
7. **RetentionPolicyService** - politicas de retencion
8. **PrivacyIncidentService** - gestion de incidentes
9. **ProcessingActivityService** - inventario de tratamientos

## Funcion Central

```python
evaluate_sensitive_access(actor_user, resource_type, resource_id, action, context)
# Retorna: allowed, mode, decision_reason, policy_snapshot, requires_exceptional_request
```

Aplica a: clinical_note, prescription, care_instruction, clinical_file, exam_result, exam_result_file, teleconsultation_meta

## Endpoints

### Patient
- `GET /api/v1/patient/privacy/consents` - listar consentimientos
- `POST /api/v1/patient/privacy/consents` - otorgar consentimiento
- `POST /api/v1/patient/privacy/consents/{id}/revoke` - revocar
- `GET /api/v1/patient/privacy/policies/active` - politicas activas
- `GET /api/v1/patient/privacy/access-log/me` - mi trazabilidad

### Professional
- `POST /api/v1/professionals/me/privacy/exceptional-access-requests`
- `GET /api/v1/professionals/me/privacy/exceptional-access-requests`
- `GET /api/v1/professionals/me/privacy/access-log/me`

### Laboratory
- `POST /api/v1/laboratories/me/privacy/exceptional-access-requests`
- `GET /api/v1/laboratories/me/privacy/exceptional-access-requests`

### Admin Privacy
- Politicas de privacidad: GET/POST /admin/privacy/policies, POST .../publish
- Politicas de recurso: GET/PUT /admin/privacy/resource-policies/{resource_type}
- Solicitudes: GET /admin/privacy/exceptional-access-requests, POST .../approve|reject|revoke
- Logs: GET /admin/privacy/access-logs, GET /admin/privacy/access-logs/export-meta
- Processing: CRUD /admin/privacy/processing-activities
- Retencion: CRUD /admin/privacy/retention-policies
- Incidentes: CRUD /admin/privacy/incidents, POST .../assign|contain|resolve|dismiss

### Privacy Auditor
- `GET /api/v1/privacy-auditor/access-logs`
- `GET /api/v1/privacy-auditor/incidents`
- `GET /api/v1/privacy-auditor/processing-activities`

## Roles Nuevos

- `admin_privacy` - gestiona solicitudes, politicas, parametros de privacidad
- `privacy_auditor` - revisa trazabilidad, sin acceso clinico

## Reglas Clave

- Admin sin grant no puede leer datos clinicos sensibles
- Acceso denegado genera `clinical_access_log` con decision=denied
- Exportes admin solo metadatos, nunca contenido clinico
- Consentimientos y politicas versionados con soft delete
- Incidentes de privacidad con maquina de estados abierta→resuelta

## Seed Data

- 5 clasificaciones de datos
- 8 politicas de recurso iniciales (clinical_note, prescription, care_instruction, etc.)
- 4 feature flags: privacy_hardening_enabled, exceptional_access_enabled, retention_policies_enabled, privacy_incidents_enabled

## Tests

15 tests cubriendo:
- Admin denegado sin grant
- Paciente accede sus propios datos
- privacy_auditor no ve contenido clinico
- Acceso denegado genera log
- Solicitud requiere justificacion
- Minutos positivos requeridos
- Aprobacion requiere expiracion futura
- Export meta excluye contenido clinico
- Incidentes con transiciones de estado
