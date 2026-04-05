# Modelo de Datos - Paso 1

## Entidades Principales

### Users
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | PK |
| email | String | Unique, index |
| password_hash | String | Argon2/Bcrypt |
| status | Enum | pending_email_verification, active, suspended, soft_deleted |
| is_email_verified | Boolean | |
| created_at, updated_at, deleted_at | DateTime | Soft delete support |
| version | String | Optimistic locking |

### People
Datos personales asociados a users.

### Patients
Extensión de People para pacientes.

### Professionals
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK -> users |
| person_id | UUID | FK -> people |
| onboarding_status | Enum | draft, submitted, under_review, approved, rejected, suspended |
| status | Enum | draft, pending_review, active, rejected, suspended |
| is_public_profile_enabled | Boolean | Solo true si verificationapproved |

### ProfessionalDocuments
Documentos cargados por profesionales (DNI, títulos, etc).
Siempre usar soft delete.

### VerificationRequests
Solicitudes de validación de profesionales.
Estado: submitted -> under_review -> approved/rejected/needs_correction

### Agreements
Términos y condiciones.
Aceptaciones guardadas con IP, user_agent y tipo de aceptación.

### AuditEvents
Log de todas las operaciones críticas.
Incluye before_json/after_json para cambios de estado.

## Relaciones

```
User 1--1 People 1--1 Patient
User 1--1 People 1--1 Professional
Professional 1--N ProfessionalDocuments
Professional 1--N ProfessionalCredentials
Professional 1--N VerificationRequests
VerificationRequest 1--N VerificationEvents
User N--N Role (via UserRole)
```

## Índices

- users.email (unique)
- people.user_id (unique)
- people.national_id
- patients.user_id (unique)
- patients.person_id (unique)
- professionals.user_id (unique)
- professionals.person_id (unique)
- professional_documents.professional_id
- verification_requests.professional_id
- audit_events.actor_user_id, occurred_at, action, entity_type, entity_id