# Paso 6 - Reviews, Reports, Moderation y Sanciones

## Resumen

Implementacion de sistema de reputacion verificable, reportes de seguridad y moderacion para el marketplace de salud.

## Tablas Nuevas

| Tabla | Descripcion |
|-------|-------------|
| `appointment_reviews` | Reseñas entre paciente y profesional |
| `appointment_review_versions` | Versionado de reseñas |
| `professional_reputation_stats` | Estadisticas agregadas de reputacion |
| `safety_reports` | Denuncias de usuarios |
| `safety_report_evidences` | Evidencias adjuntas a denuncias |
| `moderation_cases` | Casos formales de moderacion |
| `moderation_case_events` | Eventos de cada caso |
| `account_sanctions` | Sanciones reversibles |
| `trust_events` | Eventos de confianza |

## Campos Agregados

`appointments`: `patient_review_submitted`, `professional_review_submitted`

## Roles

- Nuevo rol: `admin_moderation` - puede revisar reportes, casos y sanciones

## Endpoints Principales

### Publicos
- `GET /api/v1/public/professionals/{slug}/reviews`
- `GET /api/v1/public/professionals/{slug}/rating-summary`

### Paciente
- `GET /api/v1/patient/review-eligibility`
- `POST /api/v1/patient/appointments/{id}/review-professional`
- `GET /api/v1/patient/reviews/me`
- `POST /api/v1/patient/reports`
- `GET /api/v1/patient/reports/me`

### Profesional
- `POST /api/v1/professionals/me/appointments/{id}/review-patient`
- `GET /api/v1/professionals/me/reviews/public`
- `GET /api/v1/professionals/me/reputation-summary`
- `POST /api/v1/professionals/me/reports`

### Admin Moderacion
- `GET /api/v1/admin/moderation/reports`
- `POST /api/v1/admin/moderation/reports/{id}/assign`
- `POST /api/v1/admin/moderation/reports/{id}/resolve`
- `GET /api/v1/admin/moderation/cases`
- `POST /api/v1/admin/moderation/cases`
- `POST /api/v1/admin/moderation/cases/{id}/apply-preventive-suspension`
- `POST /api/v1/admin/moderation/sanctions`
- `POST /api/v1/admin/moderation/sanctions/{id}/lift`
- `POST /api/v1/admin/moderation/reviews/{id}/hide`
- `POST /api/v1/admin/moderation/reviews/{id}/restore`

## Reglas de Visibilidad

- Patient -> Professional: `visibility=public`, `status=published`
- Professional -> Patient: `visibility=internal_only`, nunca publico

## Sanciones y sus efectos

| Tipo | Efecto |
|------|--------|
| `warning` | Solo registra, no bloquea |
| `temporary_suspension` | Bloquea operaciones durante vigencia |
| `permanent_suspension` | Bloquea definitivamente |
| `visibility_restriction` | Oculta del espacio publico |
| `review_hidden` | Oculta una review concreta |

## Feature Flags

- `reviews_enabled`
- `reports_enabled`
- `moderation_enabled`
- `sanctions_enabled`

## Archivos Creados

- `alembic/versions/005_step6.py`
- `app/models/step6_models.py`
- `app/schemas/step6_schemas.py`
- `app/services/step6_services.py`
- `app/core/moderation_authorization.py`
- `app/routers/public_reviews.py`
- `app/routers/patient_reviews.py`
- `app/routers/professional_reviews.py`
- `app/routers/laboratory_reports.py`
- `app/routers/admin_moderation.py`
- `tests/test_step6.py`
- `app_flutter/lib/features/moderation/moderation_screens.dart`

## Siguiente Paso

Paso 7: Privacidad fuerte + acceso clinico excepcional auditado + cumplimiento de datos sensibles.
