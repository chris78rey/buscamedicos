Sí, se puede. Se deja el **paso 2 masticado**, cerrado y con poco margen de interpretación, para que OpenCode implemente casi sin gastar tokens. Este paso parte de que el proyecto ya definió marketplace de salud con perfiles validados, agenda como pieza núcleo, distribución equilibrada por especialidad/zona/disponibilidad y restricción fuerte sobre datos clínicos y acceso administrativo. 

### Paso 2 para OpenCode

```text
IMPLEMENTAR PASO 2 DEL PROYECTO.

CONTEXTO FIJO
- Proyecto: marketplace de salud en Ecuador.
- Stack: Flutter + FastAPI + PostgreSQL + Docker Compose.
- Paso 1 ya existe con: auth, roles, users, patients, professionals, documents, verification, agreements, audit.
- Solo profesionales aprobados pueden aparecer públicamente.
- Admin NO puede ver datos clínicos por defecto.
- Este paso NO implementa pagos reales, videollamada, recetas, historia clínica, laboratorios ni LLM.

OBJETIVO DEL PASO 2
Implementar:
1. perfiles públicos de profesionales
2. búsqueda y filtros
3. disponibilidad semanal del profesional
4. bloqueos de horario
5. agenda base
6. creación y gestión de citas
7. historial de estados de citas
8. validaciones de seguridad y concurrencia
9. pantallas Flutter mínimas para ese flujo

NO IMPLEMENTAR
- pagos
- teleconsulta real
- videollamada
- domicilio
- recetas
- datos clínicos
- calificaciones
- comentarios
- denuncias
- laboratorios
- ranking complejo con IA
- notificaciones push reales

REGLAS DE NEGOCIO
1. Solo professionals con verification aprobada y status active pueden ser públicos.
2. Solo se muestran perfiles con is_public_profile_enabled = true.
3. La búsqueda debe usar PostgreSQL normal, sin motor semántico.
4. El paciente puede explorar sin reservar.
5. Para reservar, el paciente debe estar autenticado.
6. Un profesional no puede reservar citas consigo mismo.
7. No se puede reservar en horarios fuera de disponibilidad.
8. No se puede reservar en un slot bloqueado.
9. No se puede reservar si el slot ya fue tomado.
10. Todo cambio de estado de cita debe quedar auditado.
11. Todo cambio de cita debe dejar historial.
12. Admin puede ver datos operativos de cita, no datos clínicos.
13. Si luego existiera contenido clínico, debe quedar fuera de estos endpoints.
14. Se debe respetar soft delete y versionado.
15. La distribución visible debe ser equilibrada: no solo ordenar por rating o antigüedad.

MÓDULOS A TOCAR
- backend_api/app/domains/public_profiles
- backend_api/app/domains/specialties
- backend_api/app/domains/availability
- backend_api/app/domains/appointments
- backend_api/app/domains/audit
- app_flutter/lib/features/search
- app_flutter/lib/features/professional_public
- app_flutter/lib/features/availability
- app_flutter/lib/features/appointments

TABLAS NUEVAS

1) specialties
- id uuid pk
- code varchar unique not null
- name varchar not null
- description text null
- is_active boolean default true
- created_at
- updated_at
- deleted_at null
- version int default 1

2) professional_specialties
- id uuid pk
- professional_id fk not null
- specialty_id fk not null
- is_primary boolean default false
- created_at
- updated_at
- deleted_at null
- version int default 1
- unique(professional_id, specialty_id)

3) service_modalities
- id uuid pk
- code varchar unique not null
- name varchar not null
- is_active boolean default true
Valores seed:
- in_person_consultorio
- teleconsulta

4) professional_modalities
- id uuid pk
- professional_id fk not null
- modality_id fk not null
- is_enabled boolean default true
- created_at
- updated_at
- deleted_at null
- version int default 1
- unique(professional_id, modality_id)

5) professional_public_profiles
- id uuid pk
- professional_id fk unique not null
- public_title varchar not null
- public_bio text null
- consultation_price numeric(10,2) null
- currency_code varchar(3) default 'USD'
- province varchar null
- city varchar null
- sector varchar null
- address_reference text null
- years_experience int null
- languages_json jsonb null
- is_public boolean default false
- searchable_text text null
- created_at
- updated_at
- deleted_at null
- version int default 1

6) professional_availabilities
- id uuid pk
- professional_id fk not null
- weekday smallint not null   # 0-6
- start_time time not null
- end_time time not null
- slot_minutes int not null
- modality_code varchar not null
- status varchar not null default 'active'
- created_at
- updated_at
- deleted_at null
- version int default 1

7) professional_time_blocks
- id uuid pk
- professional_id fk not null
- starts_at timestamptz not null
- ends_at timestamptz not null
- reason varchar null
- block_type varchar not null   # manual, vacation, admin, external
- created_at
- updated_at
- deleted_at null
- version int default 1

8) appointments
- id uuid pk
- public_code varchar unique not null
- patient_id fk not null
- professional_id fk not null
- modality_code varchar not null
- scheduled_start timestamptz not null
- scheduled_end timestamptz not null
- timezone varchar not null default 'America/Guayaquil'
- status varchar not null
- patient_note varchar(500) null
- admin_note varchar(500) null
- cancellation_reason varchar(300) null
- reschedule_reason varchar(300) null
- created_from varchar not null default 'patient_app'
- created_at
- updated_at
- deleted_at null
- version int default 1

9) appointment_status_history
- id uuid pk
- appointment_id fk not null
- old_status varchar null
- new_status varchar not null
- changed_by_user_id fk null
- reason varchar null
- created_at

10) professional_search_impressions
- id uuid pk
- professional_id fk not null
- viewer_user_id fk null
- search_session_id varchar null
- position int not null
- created_at

ESTADOS DE CITA
- pending_confirmation
- confirmed
- cancelled_by_patient
- cancelled_by_professional
- completed
- no_show_patient
- no_show_professional

TRANSICIONES
- pending_confirmation -> confirmed
- pending_confirmation -> cancelled_by_patient
- pending_confirmation -> cancelled_by_professional
- confirmed -> cancelled_by_patient
- confirmed -> cancelled_by_professional
- confirmed -> completed
- confirmed -> no_show_patient
- confirmed -> no_show_professional
No permitir otras.

REGLAS DE DISPONIBILIDAD
1. start_time < end_time
2. slot_minutes permitido: 15, 20, 30, 45, 60
3. no permitir traslapes entre availabilities activas del mismo professional y misma modality
4. no permitir time_blocks inválidos
5. al consultar slots disponibles, excluir:
   - slots fuera de availability
   - slots bloqueados
   - slots ocupados por appointments pending_confirmation o confirmed

REGLAS DE PERFIL PÚBLICO
1. Solo si professional.status = active
2. Solo si onboarding_status = approved
3. Solo si public profile is_public = true
4. Nunca exponer:
   - documentos subidos
   - notas internas de verificación
   - email privado
   - cédula
   - agreement evidence
5. Sí exponer:
   - nombre público
   - título público
   - bio pública
   - especialidades
   - ciudad/provincia/sector
   - modalidades activas
   - idiomas
   - años experiencia
   - precio referencial si existe

REGLAS DE BÚSQUEDA
Filtros:
- specialty
- province
- city
- modality
- min_price
- max_price
- available_date
- available_from
- available_to

Orden por defecto:
- equilibrio simple: mezclar score base + rotación
Implementación simple:
- score_base por coincidencia de filtros
- luego ordenar por last_shown_at asc nulls first, updated_at desc
- actualizar professional_search_impressions solo cuando se muestran resultados
No implementar ranking complejo.

ENDPOINTS NUEVOS

PUBLIC
- GET /api/v1/public/specialties
- GET /api/v1/public/professionals
- GET /api/v1/public/professionals/{public_slug}
- GET /api/v1/public/professionals/{professional_id}/slots?date=YYYY-MM-DD&modality=teleconsulta

PROFESSIONAL SELF
- GET /api/v1/professionals/me/public-profile
- PUT /api/v1/professionals/me/public-profile
- GET /api/v1/professionals/me/specialties
- PUT /api/v1/professionals/me/specialties
- GET /api/v1/professionals/me/modalities
- PUT /api/v1/professionals/me/modalities
- GET /api/v1/professionals/me/availabilities
- POST /api/v1/professionals/me/availabilities
- PUT /api/v1/professionals/me/availabilities/{id}
- DELETE /api/v1/professionals/me/availabilities/{id}
- GET /api/v1/professionals/me/time-blocks
- POST /api/v1/professionals/me/time-blocks
- DELETE /api/v1/professionals/me/time-blocks/{id}
- GET /api/v1/professionals/me/appointments
- POST /api/v1/professionals/me/appointments/{id}/confirm
- POST /api/v1/professionals/me/appointments/{id}/cancel
- POST /api/v1/professionals/me/appointments/{id}/complete
- POST /api/v1/professionals/me/appointments/{id}/mark-no-show-patient

PATIENT
- POST /api/v1/patient/appointments
- GET /api/v1/patient/appointments
- GET /api/v1/patient/appointments/{id}
- POST /api/v1/patient/appointments/{id}/cancel

ADMIN
- GET /api/v1/admin/appointments
- GET /api/v1/admin/appointments/{id}
- GET /api/v1/admin/audit-events?entity_type=appointment

REQUEST/RESPONSE CLAVES

POST /patient/appointments
input:
- professional_id
- modality_code
- scheduled_start
- patient_note optional
output:
- appointment id
- public_code
- status
- scheduled_start
- scheduled_end

PUT /professionals/me/public-profile
input:
- public_title
- public_bio
- consultation_price
- province
- city
- sector
- years_experience
- languages_json
- is_public

GET /public/professionals
output por item:
- professional_id
- public_slug
- public_display_name
- public_title
- specialties[]
- province
- city
- sector
- modalities[]
- years_experience
- consultation_price
- next_available_at optional

VALIDACIONES
- paciente autenticado para reservar
- professional activo y público
- specialty existente
- modality válida y activa para ese professional
- slot disponible de verdad
- optimistic locking con version
- timezone fija inicial: America/Guayaquil
- duración del slot = slot_minutes de availability

CONCURRENCIA
Al reservar cita:
1. iniciar transacción
2. validar professional activo
3. resolver availability aplicable
4. verificar ausencia de block
5. verificar ausencia de cita ocupando ese slot con lock
6. crear appointment pending_confirmation
7. registrar appointment_status_history
8. registrar audit_event
9. commit
Usar índice y validación robusta para evitar doble reserva.

ÍNDICES MÍNIMOS
- specialties(code)
- professional_specialties(professional_id, specialty_id)
- professional_public_profiles(is_public, province, city)
- professional_availabilities(professional_id, weekday, modality_code)
- professional_time_blocks(professional_id, starts_at, ends_at)
- appointments(professional_id, scheduled_start, scheduled_end, status)
- appointments(patient_id, created_at desc)
- appointments(public_code)

SEEDS
- specialties básicas
- service_modalities
- feature_flag: public_profiles_enabled=true
- feature_flag: appointments_enabled=true

AUDITORÍA OBLIGATORIA
Registrar audit_event en:
- crear/editar perfil público
- crear/editar/deletar availability
- crear/deletar time block
- crear cita
- confirmar cita
- cancelar cita
- completar cita
- marcar no show

PANTALLAS FLUTTER MÍNIMAS

PACIENTE
1. buscador de profesionales
2. lista de resultados con filtros
3. detalle de perfil público
4. selector de fecha/modalidad
5. slots disponibles
6. confirmar reserva
7. listado de mis citas

PROFESSIONAL
1. editar perfil público
2. gestionar especialidades
3. gestionar modalidades
4. gestionar availability semanal
5. gestionar bloqueos
6. listado de citas
7. confirmar/cancelar/completar cita

ADMIN
1. listado simple de citas
2. detalle operativo simple
3. acceso a auditoría de citas

NO HACER UI COMPLEJA
- diseño simple
- sin estado global complejo si no hace falta
- usar cliente HTTP limpio
- manejar loading/error/empty

PRUEBAS AUTOMÁTICAS
1. professional no aprobado no aparece en público
2. professional aprobado y público sí aparece
3. búsqueda por specialty funciona
4. búsqueda por city funciona
5. slot se genera correctamente
6. no se muestran slots bloqueados
7. no se permite doble reserva del mismo slot
8. patient puede cancelar cita pending_confirmation o confirmed
9. professional puede confirmar cita pending_confirmation
10. transición inválida falla
11. audit_event se registra
12. appointment_status_history se registra
13. admin no recibe datos clínicos
14. soft delete de availability no rompe historial
15. soft delete de time block funciona

ORDEN EXACTO DE IMPLEMENTACIÓN
1. migraciones nuevas
2. seeds
3. modelos ORM
4. schemas pydantic
5. repositorios/servicios de specialties
6. public_profile
7. availabilities
8. time_blocks
9. slot generation service
10. appointment booking service con transacción
11. state machine de appointment
12. endpoints backend
13. tests backend
14. pantallas Flutter
15. integración Flutter-API
16. README paso 2

CRITERIOS DE ACEPTACIÓN
- se puede buscar profesionales públicos
- se puede ver detalle público
- se pueden consultar slots
- un paciente autenticado puede reservar
- un professional puede confirmar/cancelar/completar
- no existe doble booking
- todo cambio crítico queda auditado
- admin no ve contenido clínico
- tests pasan

SALIDA ESPERADA
Entregar directamente:
- migraciones
- modelos
- endpoints
- servicios
- tests
- pantallas Flutter mínimas
- README breve

NO EXPLICAR DEMASIADO
IMPLEMENTAR.
```

### Versión todavía más corta

Si se desea gastar menos tokens aún, basta con pegar esto:

```text
Implementar paso 2 del marketplace de salud:
perfiles públicos + especialidades + modalidades + disponibilidades + bloqueos + slots + citas + historial de estados + auditoría.

Stack existente:
FastAPI + PostgreSQL + Flutter.
Paso 1 ya tiene auth, roles, professional verification, audit base.

No implementar:
pagos, videollamada, telemedicina real, clínica, recetas, reputación, laboratorios, IA.

Reglas:
- solo professional aprobado y activo puede ser público
- búsqueda por PostgreSQL: specialty, province, city, modality, price
- paciente autenticado puede reservar
- no doble booking
- no reservar fuera de disponibilidad ni en bloqueos
- cada cambio de cita auditable
- admin solo ve datos operativos, no clínicos

Crear tablas:
specialties
professional_specialties
service_modalities
professional_modalities
professional_public_profiles
professional_availabilities
professional_time_blocks
appointments
appointment_status_history
professional_search_impressions

Estados cita:
pending_confirmation
confirmed
cancelled_by_patient
cancelled_by_professional
completed
no_show_patient
no_show_professional

Endpoints:
GET /public/specialties
GET /public/professionals
GET /public/professionals/{slug}
GET /public/professionals/{id}/slots?date=YYYY-MM-DD&modality=teleconsulta

GET/PUT /professionals/me/public-profile
GET/PUT /professionals/me/specialties
GET/PUT /professionals/me/modalities
CRUD /professionals/me/availabilities
CRUD /professionals/me/time-blocks
GET /professionals/me/appointments
POST /professionals/me/appointments/{id}/confirm
POST /professionals/me/appointments/{id}/cancel
POST /professionals/me/appointments/{id}/complete

POST /patient/appointments
GET /patient/appointments
GET /patient/appointments/{id}
POST /patient/appointments/{id}/cancel

GET /admin/appointments
GET /admin/appointments/{id}
GET /admin/audit-events?entity_type=appointment

Implementar:
- migraciones
- modelos ORM
- servicios
- state machine de citas
- tests
- Flutter mínimo: buscador, detalle profesional, slots, reserva, mis citas, agenda del profesional

Tests:
- profesional no aprobado no aparece
- filtros funcionan
- slots correctos
- bloqueos excluyen slots
- no doble reserva
- transiciones válidas e inválidas
- auditoría creada
- admin sin acceso clínico

Entregar código, sin explicación larga.
```

La primera versión es más segura. La segunda consume menos tokens.

Luego convendría preparar el **paso 3** igual de comprimido: **pagos + comisión + confirmación económica de la cita**.
