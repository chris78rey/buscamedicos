Se deja el **paso 6 masticado** para OpenCode: **calificaciones verificadas + comentarios + denuncias + moderación + suspensión de perfiles**, alineado con la necesidad de reputación basada en atenciones verificadas, revisión de denuncias, moderación y bloqueo de perfiles riesgosos. 

```text id="61852"
IMPLEMENTAR PASO 6 DEL MARKETPLACE DE SALUD.

CONTEXTO FIJO
- Stack: Flutter + FastAPI + PostgreSQL + Docker Compose.
- Paso 1 ya existe: auth, roles, verification, agreements, audit.
- Paso 2 ya existe: perfiles públicos, disponibilidades, citas.
- Paso 3 ya existe: pagos y comisión.
- Paso 4 ya existe: teleconsulta básica, nota clínica simple, receta, indicaciones.
- Paso 5 ya existe: órdenes de examen, laboratorios y resultados.
- No cambiar arquitectura.
- Mantener soft delete, auditoría, versionado, estados y reversibilidad.
- Admin NO puede ver datos clínicos por defecto.
- La plataforma sigue siendo intermediario tecnológico.

OBJETIVO
Implementar:
1. calificaciones verificadas después de atenciones completadas
2. comentarios públicos controlados para profesionales
3. evaluación interna del paciente por el profesional, no pública
4. denuncias o reportes con evidencia
5. casos de moderación
6. sanciones y suspensiones reversibles
7. ocultamiento de reviews o perfiles riesgosos
8. trazabilidad completa de decisiones
9. pantallas Flutter mínimas

NO IMPLEMENTAR
- reputación con IA
- ranking avanzado
- sistema antifraude complejo con ML
- mensajería entre partes
- arbitraje legal externo
- scoring crediticio
- comentarios públicos para pacientes
- patrocinados
- moderación automática compleja de lenguaje

ENFOQUE
Implementar reputación verificable y seguridad operativa:
- solo se puede calificar tras una cita completed
- patient -> professional = reseña pública posible
- professional -> patient = evaluación interna, no pública
- cualquier parte puede denunciar
- admin_moderation revisa, documenta y sanciona si aplica
- toda sanción es reversible por estado, nunca borrado físico

ROLES NUEVOS
Agregar:
- admin_moderation

REGLAS DE ROLES
- admin_moderation puede revisar reseñas reportadas, denuncias, casos y sanciones
- admin_moderation puede suspender preventivamente perfiles con auditoría
- admin_moderation NO puede ver contenido clínico por endpoints normales
- admin_support solo ve datos operativos si ya existe en paso 1
- super_admin conserva gobierno técnico, pero tampoco ve clínico por defecto

REGLAS DE NEGOCIO
1. Solo citas con status = completed permiten review.
2. Solo citas reales y verificadas permiten review.
3. Una misma dirección de review solo una vez por cita.
4. patient puede dejar review pública al professional.
5. professional puede dejar evaluación interna del patient, no pública.
6. No se permiten reviews anónimas entre partes.
7. Las reviews públicas deben poder ocultarse por moderación, no borrarse físicamente.
8. Cualquier usuario autenticado puede denunciar a otro usuario, una review, una cita o un laboratorio.
9. Toda denuncia debe permitir evidencia opcional.
10. Toda denuncia debe entrar a flujo formal de revisión.
11. La suspensión preventiva debe quedar documentada con motivo y duración.
12. Las sanciones no eliminan historial previo.
13. Un professional con sanción activa de suspensión no debe aparecer en búsqueda pública ni aceptar nuevas citas.
14. Un patient con sanción activa de suspensión no debe poder reservar nuevas citas.
15. Un laboratory con sanción activa no debe aparecer en opciones públicas ni aceptar nuevas órdenes.
16. Las reviews públicas deben agregarse a reputación del professional.
17. Las evaluaciones internas de patient no se muestran públicamente.
18. Admin nunca debe recibir contenido clínico en endpoints de moderación.
19. Toda lectura y escritura de moderación debe quedar auditada.
20. Toda resolución debe ser reversible mediante levantamiento o expiración de sanción.

TABLAS NUEVAS

1) appointment_reviews
- id uuid pk
- appointment_id fk not null
- reviewer_user_id fk not null
- reviewer_role_code varchar not null   # patient, professional
- target_user_id fk not null
- target_role_code varchar not null     # professional, patient
- rating_overall smallint not null      # 1..5
- rating_punctuality smallint null
- rating_communication smallint null
- rating_respect smallint null
- comment_text text null
- visibility varchar not null           # public, internal_only
- status varchar not null               # published, hidden, withdrawn
- moderation_flag boolean default false
- created_at
- updated_at
- deleted_at null
- version int default 1
- unique(appointment_id, reviewer_user_id, target_user_id)

2) appointment_review_versions
- id uuid pk
- review_id fk not null
- version_number int not null
- snapshot_json jsonb not null
- changed_by_user_id fk not null
- change_reason varchar null
- created_at

3) professional_reputation_stats
- id uuid pk
- professional_id fk unique not null
- public_reviews_count int not null default 0
- avg_overall numeric(4,2) not null default 0
- avg_punctuality numeric(4,2) not null default 0
- avg_communication numeric(4,2) not null default 0
- avg_respect numeric(4,2) not null default 0
- hidden_reviews_count int not null default 0
- last_calculated_at timestamptz not null
- version int default 1

4) safety_reports
- id uuid pk
- reporter_user_id fk not null
- subject_type varchar not null         # professional, patient, laboratory, review, appointment
- subject_id uuid not null
- appointment_id fk null
- category_code varchar not null        # abuse, fraud, harassment, impersonation, no_show, unsafe_behavior, fake_profile, inappropriate_review, other
- severity_claimed varchar not null     # low, medium, high, critical
- description text not null
- is_counterparty_hidden boolean default true
- status varchar not null               # submitted, under_review, action_required, resolved, rejected, escalated
- submitted_at timestamptz not null
- assigned_admin_id fk null
- resolved_at timestamptz null
- resolution_summary text null
- created_at
- updated_at
- deleted_at null
- version int default 1

5) safety_report_evidences
- id uuid pk
- report_id fk not null
- file_id fk not null
- evidence_type varchar not null        # image, pdf, audio, screenshot, other
- created_at
- updated_at
- deleted_at null
- version int default 1

6) moderation_cases
- id uuid pk
- source_type varchar not null          # report, manual, system
- source_id uuid null
- target_type varchar not null          # professional, patient, laboratory, review
- target_id uuid not null
- status varchar not null               # open, under_review, preventive_action, resolved, dismissed
- priority varchar not null             # low, medium, high, critical
- assigned_admin_id fk null
- opened_at timestamptz not null
- closed_at timestamptz null
- outcome_code varchar null             # no_action, warning, temporary_suspension, permanent_suspension, review_hidden, profile_hidden
- outcome_summary text null
- created_at
- updated_at
- deleted_at null
- version int default 1

7) moderation_case_events
- id uuid pk
- moderation_case_id fk not null
- event_type varchar not null           # opened, assigned, note_added, preventive_suspension, review_hidden, sanction_applied, sanction_lifted, resolved, dismissed
- event_payload_json jsonb null
- created_by_user_id fk not null
- created_at

8) account_sanctions
- id uuid pk
- target_type varchar not null          # professional, patient, laboratory, review
- target_id uuid not null
- sanction_type varchar not null        # warning, temporary_suspension, permanent_suspension, visibility_restriction, review_hidden
- reason_code varchar not null
- reason_text text null
- starts_at timestamptz not null
- ends_at timestamptz null
- status varchar not null               # active, lifted, expired
- applied_by_user_id fk not null
- lifted_by_user_id fk null
- lifted_reason text null
- moderation_case_id fk null
- created_at
- updated_at
- deleted_at null
- version int default 1

9) trust_events
- id uuid pk
- target_type varchar not null          # professional, patient, laboratory
- target_id uuid not null
- event_code varchar not null           # completed_review, report_created, report_resolved, sanction_applied, sanction_lifted
- weight int not null default 0
- metadata_json jsonb null
- created_at

CAMBIOS A TABLAS EXISTENTES

appointments
agregar:
- patient_review_submitted boolean default false
- professional_review_submitted boolean default false

professionals
no cambiar estructura principal, pero la visibilidad efectiva debe respetar sanciones activas

patients
no cambiar estructura principal, pero la reserva efectiva debe respetar sanciones activas

laboratories
si existen del paso 5, la visibilidad y operación deben respetar sanciones activas

MÁQUINAS DE ESTADO

appointment_reviews.status
- published
- hidden
- withdrawn

Transiciones:
- published -> hidden
- published -> withdrawn
- hidden -> published

safety_reports.status
- submitted
- under_review
- action_required
- resolved
- rejected
- escalated

Transiciones:
- submitted -> under_review
- under_review -> action_required
- under_review -> resolved
- under_review -> rejected
- under_review -> escalated
- action_required -> resolved

moderation_cases.status
- open
- under_review
- preventive_action
- resolved
- dismissed

Transiciones:
- open -> under_review
- under_review -> preventive_action
- under_review -> resolved
- under_review -> dismissed
- preventive_action -> resolved

account_sanctions.status
- active
- lifted
- expired

Transiciones:
- active -> lifted
- active -> expired

REGLAS DE VISIBILIDAD DE REVIEW
1. patient -> professional:
   - visibility = public
   - status inicial = published
   - si es reportada o moderada puede pasar a hidden
2. professional -> patient:
   - visibility = internal_only
   - nunca aparece públicamente
   - solo sirve para seguridad/moderación interna
3. comentarios internos jamás se exponen al target públicamente si la política no lo permite
4. no mostrar nombre del reviewer paciente de forma excesiva si se decide anonimización pública parcial
Implementación simple:
- en review pública mostrar nombre abreviado del paciente, por ejemplo “C. R.”
- guardar nombre real internamente, exponer versión abreviada en API pública

REGLAS DE CÁLCULO DE REPUTACIÓN
Solo contar en professional_reputation_stats:
- reviews visibility public
- reviews status published
- target_role_code professional
Excluir:
- hidden
- withdrawn
- internal_only

REGLAS DE DENUNCIA
1. El reporter debe ser usuario autenticado.
2. Debe existir subject_type y subject_id válidos.
3. Debe existir descripción mínima.
4. Puede adjuntar evidencias.
5. Puede denunciar:
   - professional
   - patient
   - laboratory
   - review
   - appointment
6. Si la severidad es critical, permitir marca rápida para cola prioritaria.
7. Crear moderation_case manual o automático según configuración simple.
8. No mostrar al denunciado quién denunció si is_counterparty_hidden = true.

REGLAS DE SANCIONES
1. warning: no bloquea acceso, solo registra.
2. temporary_suspension:
   - bloquea nuevas operaciones clave del target durante la vigencia
3. permanent_suspension:
   - bloquea definitivamente nuevas operaciones hasta levantamiento administrativo explícito si la política lo permite
4. visibility_restriction:
   - oculta perfil o review del espacio público
5. review_hidden:
   - oculta una review concreta
6. Las sanciones activas deben evaluarse en:
   - búsqueda pública
   - creación de citas
   - aceptación de órdenes de laboratorio
   - creación de nuevo contenido público relevante

REGLAS DE ACCESO
1. patient solo puede crear y ver sus propias reviews emitidas y reportes emitidos.
2. professional solo puede crear evaluación de citas completadas en las que participó.
3. target de review no puede editar la review.
4. admin_moderation puede ver:
   - datos operativos de cita
   - review pública o interna necesaria para moderación
   - reportes y evidencias
   - historial de sanciones
   - NUNCA nota clínica completa, receta, indicaciones ni resultados clínicos
5. endpoints de moderación deben usar require_moderation_scope().
6. toda lectura de reportes/casos/sanciones debe quedar en audit_event.
7. toda acción sobre review reportada, caso o sanción debe quedar en audit_event y moderation_case_events cuando aplique.

ENDPOINTS NUEVOS

PUBLIC
- GET /api/v1/public/professionals/{public_slug}/reviews
- GET /api/v1/public/professionals/{public_slug}/rating-summary

PATIENT
- GET /api/v1/patient/review-eligibility
- POST /api/v1/patient/appointments/{id}/review-professional
- GET /api/v1/patient/reviews/me
- POST /api/v1/patient/reports
- GET /api/v1/patient/reports/me
- GET /api/v1/patient/reports/{id}

PROFESSIONAL
- POST /api/v1/professionals/me/appointments/{id}/review-patient
- GET /api/v1/professionals/me/reviews/public
- GET /api/v1/professionals/me/reputation-summary
- POST /api/v1/professionals/me/reports
- GET /api/v1/professionals/me/reports/me
- GET /api/v1/professionals/me/reports/{id}

LABORATORY
- POST /api/v1/laboratories/me/reports
- GET /api/v1/laboratories/me/reports/me

ADMIN MODERATION
- GET /api/v1/admin/moderation/reports
- GET /api/v1/admin/moderation/reports/{id}
- POST /api/v1/admin/moderation/reports/{id}/assign
- POST /api/v1/admin/moderation/reports/{id}/mark-under-review
- POST /api/v1/admin/moderation/reports/{id}/resolve
- POST /api/v1/admin/moderation/reports/{id}/reject

- GET /api/v1/admin/moderation/cases
- GET /api/v1/admin/moderation/cases/{id}
- POST /api/v1/admin/moderation/cases
- POST /api/v1/admin/moderation/cases/{id}/add-note
- POST /api/v1/admin/moderation/cases/{id}/apply-preventive-suspension
- POST /api/v1/admin/moderation/cases/{id}/resolve
- POST /api/v1/admin/moderation/cases/{id}/dismiss

- GET /api/v1/admin/moderation/reviews
- POST /api/v1/admin/moderation/reviews/{id}/hide
- POST /api/v1/admin/moderation/reviews/{id}/restore
- GET /api/v1/admin/moderation/sanctions
- POST /api/v1/admin/moderation/sanctions
- POST /api/v1/admin/moderation/sanctions/{id}/lift

REQUEST/RESPONSE CLAVES

POST /patient/appointments/{id}/review-professional
input:
- rating_overall
- rating_punctuality optional
- rating_communication optional
- rating_respect optional
- comment_text optional
output:
- review_id
- status
- visibility
- target_user_id

POST /professionals/me/appointments/{id}/review-patient
input:
- rating_overall
- rating_respect optional
- comment_text optional
output:
- review_id
- status
- visibility=internal_only

POST /patient/reports
input:
- subject_type
- subject_id
- appointment_id optional
- category_code
- severity_claimed
- description
- evidence_files optional
output:
- report_id
- status
- submitted_at

POST /admin/moderation/sanctions
input:
- target_type
- target_id
- sanction_type
- reason_code
- reason_text
- starts_at
- ends_at optional
- moderation_case_id optional
output:
- sanction_id
- status

GET /public/professionals/{slug}/rating-summary
output:
- professional_id
- public_reviews_count
- avg_overall
- avg_punctuality
- avg_communication
- avg_respect

VALIDACIONES
1. Solo completed permite review.
2. reviewer debe pertenecer a la cita.
3. no review duplicada por dirección.
4. no self-review.
5. rating_overall entre 1 y 5.
6. comment_text con límite razonable.
7. review pública solo patient -> professional.
8. review interna solo professional -> patient.
9. report debe tener subject válido.
10. no aplicar sanción sin reason_code.
11. temporary_suspension debe tener ends_at.
12. permanent_suspension puede no tener ends_at.
13. hide review no borra review.
14. restore review solo aplica si no hay sanción activa incompatible.
15. professional suspendido no aparece en búsqueda pública.
16. patient suspendido no puede crear nuevas citas.
17. laboratory suspendido no aparece en opciones públicas.
18. admin_moderation no puede acceder a endpoints clínicos.
19. toda resolución debe dejar resumen.

SERVICIOS
1. review service
2. reputation aggregation service
3. report service
4. moderation case service
5. sanction enforcement service
6. moderation authorization service
7. moderation audit service

AUDITORÍA OBLIGATORIA
Registrar audit_event en:
- crear review
- ocultar/restaurar review
- crear report
- asignar report
- abrir caso
- agregar nota de caso
- aplicar sanción
- levantar sanción
- resolver o descartar caso
- consultar listado y detalle de moderación

ARCHIVOS
- evidencias de reportes usan storage existente
- access_level = sensitive
- sha256 obligatorio
- tamaño máximo configurable
- validación mime/extensión
- solo personal de moderación autorizado ve evidencias

EFECTO DE SANCIONES EN OTROS MÓDULOS
Implementar chequeo reusable:
- is_target_restricted(target_type, target_id, action_code)
Acciones mínimas:
- professional_public_visibility
- professional_can_receive_booking
- patient_can_book
- laboratory_public_visibility
- laboratory_can_accept_order

PRUEBAS AUTOMÁTICAS
1. patient puede review de cita completed
2. patient no puede review de cita no completed
3. professional puede review interna de patient tras cita completed
4. professional review no aparece pública
5. no se permite review duplicada por dirección
6. review pública actualiza reputation stats
7. hide review recalcula reputation stats
8. report se crea con evidencia
9. admin_moderation puede asignar y resolver report
10. preventive suspension bloquea acciones del target
11. lift sanction restablece acciones permitidas
12. professional suspendido desaparece del público
13. patient suspendido no puede reservar
14. laboratory suspendido no aparece en selección
15. admin_moderation no ve contenido clínico
16. audit_event se registra en flujos de moderación
17. moderation_case_events se registran
18. withdrawn review no cuenta para reputación

PANTALLAS FLUTTER MÍNIMAS

PUBLIC/PATIENT
1. ver resumen de rating del professional
2. ver listado de reviews públicas
3. dejar review después de cita completed
4. crear report con evidencia
5. ver estado de reportes propios

PROFESSIONAL
1. ver reviews públicas recibidas
2. ver resumen de reputación
3. evaluar internamente al patient después de cita completed
4. crear report
5. ver sus reportes propios

LABORATORY
1. crear report
2. ver reportes propios

ADMIN MODERATION
1. listado de reportes
2. detalle de reporte
3. listado de casos
4. detalle de caso
5. ocultar/restaurar review
6. aplicar/levantar sanción
7. resolver/descartar caso
8. ver solo datos operativos, nunca clínicos

NO HACER UI COMPLEJA
- diseño simple
- loading/error/empty
- cliente HTTP limpio
- sin optimización prematura

SEEDS
- feature_flag reviews_enabled=true
- feature_flag reports_enabled=true
- feature_flag moderation_enabled=true
- feature_flag sanctions_enabled=true

ORDEN EXACTO DE IMPLEMENTACIÓN
1. migraciones
2. seeds
3. modelos ORM
4. schemas
5. review service
6. reputation aggregation service
7. report service
8. moderation case service
9. sanction enforcement service
10. endpoints
11. tests backend
12. pantallas Flutter
13. integración Flutter-API
14. README paso 6

CRITERIOS DE ACEPTACIÓN
- patient puede dejar review pública tras cita completed
- professional puede evaluar internamente a patient
- reputación pública se calcula bien
- reportes pueden crearse con evidencia
- admin_moderation puede abrir caso y sancionar
- sanciones afectan visibilidad y operaciones
- admin no ve contenido clínico
- todo queda auditado
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

```text id="17436"
Implementar paso 6:
reviews verificadas + reputación + reportes + moderación + sanciones.

Base existente:
FastAPI + PostgreSQL + Flutter.
Pasos 1 a 5 ya existen.

No implementar:
IA reputacional, ranking complejo, antifraude ML, comentarios públicos para patients.

Agregar rol:
- admin_moderation

Crear tablas:
appointment_reviews
appointment_review_versions
professional_reputation_stats
safety_reports
safety_report_evidences
moderation_cases
moderation_case_events
account_sanctions
trust_events

Agregar a appointments:
- patient_review_submitted boolean
- professional_review_submitted boolean

Reglas:
- solo citas completed permiten review
- patient -> professional = pública
- professional -> patient = internal_only
- una review por dirección por cita
- reportes con evidencia
- moderación con caso formal
- sanciones reversibles por estado
- professional suspendido no aparece en público ni recibe citas
- patient suspendido no reserva
- laboratory suspendido no aparece ni acepta órdenes
- admin_moderation no ve clínico

Estados:
review.status = published, hidden, withdrawn
report.status = submitted, under_review, action_required, resolved, rejected, escalated
case.status = open, under_review, preventive_action, resolved, dismissed
sanction.status = active, lifted, expired

Endpoints:
GET /public/professionals/{slug}/reviews
GET /public/professionals/{slug}/rating-summary

GET /patient/review-eligibility
POST /patient/appointments/{id}/review-professional
GET /patient/reviews/me
POST /patient/reports
GET /patient/reports/me
GET /patient/reports/{id}

POST /professionals/me/appointments/{id}/review-patient
GET /professionals/me/reviews/public
GET /professionals/me/reputation-summary
POST /professionals/me/reports
GET /professionals/me/reports/me

POST /laboratories/me/reports
GET /laboratories/me/reports/me

GET /admin/moderation/reports
GET /admin/moderation/reports/{id}
POST /admin/moderation/reports/{id}/assign
POST /admin/moderation/reports/{id}/mark-under-review
POST /admin/moderation/reports/{id}/resolve
POST /admin/moderation/reports/{id}/reject

GET /admin/moderation/cases
GET /admin/moderation/cases/{id}
POST /admin/moderation/cases
POST /admin/moderation/cases/{id}/add-note
POST /admin/moderation/cases/{id}/apply-preventive-suspension
POST /admin/moderation/cases/{id}/resolve
POST /admin/moderation/cases/{id}/dismiss

GET /admin/moderation/reviews
POST /admin/moderation/reviews/{id}/hide
POST /admin/moderation/reviews/{id}/restore
GET /admin/moderation/sanctions
POST /admin/moderation/sanctions
POST /admin/moderation/sanctions/{id}/lift

Tests:
- no review sin cita completed
- no review duplicada
- professional internal review no pública
- reputation stats correctos
- report con evidencia
- suspensión bloquea operaciones
- lift restablece
- admin no ve clínico
- auditoría funciona

Entregar código, migraciones, tests, Flutter mínimo y README.
```

Luego correspondería el **paso 7**: **privacidad fuerte + acceso clínico excepcional auditado + cumplimiento reforzado de datos sensibles**.
