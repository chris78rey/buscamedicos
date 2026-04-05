Se propone que el **paso 1** no sea agenda, pagos ni videollamada todavía. Se propone que el primer paso sea la **fundación segura del sistema**, porque ya están cerradas varias decisiones clave: el producto será un marketplace de salud en Ecuador, con validación documental manual de profesionales, enfoque de intermediario tecnológico, desarrollo local primero, stack Flutter + FastAPI + PostgreSQL + Docker Compose, uso inicial de IA solo como apoyo no clínico, y restricción fuerte para que los administradores no vean datos clínicos salvo acceso excepcional auditado.   

El paso 1 recomendado es:

**“Base segura del proyecto + autenticación + roles + auditoría + onboarding y validación de profesionales”**

Si ese paso queda bien hecho, los siguientes pasos se vuelven mucho más rápidos y con menos retrabajo. Si queda mal hecho, todo lo demás nace frágil.

A continuación se deja el texto listo para pegar a otro LLM.

```text
ACTUAR COMO ARQUITECTO SENIOR Y DESARROLLADOR FULL STACK PARA CONSTRUIR EL PASO 1 DE UNA PLATAFORMA DE SALUD EN ECUADOR.

IMPORTANTE
Este modelo NO debe asumir contexto previo. Todo lo necesario está descrito aquí. No debe pedir aclaraciones innecesarias. Debe tomar decisiones razonables, documentarlas y avanzar.

NOMBRE DEL PROYECTO
Marketplace de salud en Ecuador para conectar pacientes, profesionales de salud y, más adelante, laboratorios/centros diagnósticos.

OBJETIVO DEL NEGOCIO
Construir una plataforma legal, auditable y escalable que permita:
- registro y validación de profesionales
- búsqueda futura de profesionales por pacientes
- atención inicial en consultorio y teleconsulta
- monetización por comisión y planes
- protección fuerte de datos personales y clínicos
- crecimiento posterior hacia recetas, órdenes, resultados, reputación, laboratorios y pagos completos

DECISIONES YA TOMADAS Y QUE NO DEBEN CAMBIARSE
1. La plataforma operará como intermediario tecnológico y comercial, no como prestador directo de atención clínica.
2. La primera versión funcional del producto completo será un marketplace de salud con perfiles validados, agenda, pagos, atención presencial en consultorio y teleconsulta básica.
3. La atención a domicilio NO se implementará en el paso 1.
4. La validación de profesionales será documental y manual antes de publicar el perfil.
5. Los administradores NO deben poder ver datos clínicos libremente.
6. Toda operación crítica debe ser auditable.
7. Toda operación crítica debe ser reversible o compensable.
8. Nunca se debe borrar físicamente información crítica.
9. Debe usarse soft delete, versionado, bitácora y estados.
10. Debe existir RBAC + relación asistencial + control contextual.
11. Toda entidad crítica debe tener historial de cambios.
12. El desarrollo inicial será LOCAL con Docker Compose.
13. El stack principal será:
   - frontend: Flutter + Dart
   - backend: FastAPI + Python
   - base de datos: PostgreSQL
   - cache/colas: Redis, pero en este paso debe quedar opcional por perfil
   - infraestructura local: Docker Compose
14. El backend será un monolito modular, no microservicios.
15. La IA con OpenRouter se usará después y solo como apoyo no clínico.
16. Se debe priorizar bajo consumo de RAM y parametrización por .env.

OBJETIVO ESPECÍFICO DEL PASO 1
Construir la base técnica y funcional mínima, segura y extensible del sistema, incluyendo:
- estructura del monorepo
- Docker Compose local mínimo
- backend FastAPI modular
- autenticación
- autorización por roles
- auditoría base
- versionado base
- soft delete base
- estados de usuario y validación profesional
- registro de paciente
- registro de profesional
- carga de documentos del profesional
- flujo de revisión administrativa de profesionales
- firma/aceptación formal de acuerdos
- protección explícita para impedir acceso administrativo libre a datos clínicos
- pruebas automáticas
- documentación para correr todo en local

NO IMPLEMENTAR TODAVÍA
- pagos reales
- agenda completa
- citas completas
- teleconsulta real
- videollamada
- recetas clínicas completas
- historia clínica completa
- órdenes y resultados completos
- reputación/calificaciones
- integración con laboratorios
- OpenRouter
- notificaciones push reales
- panel comercial público
- ranking de médicos
- búsqueda semántica

ALCANCE FUNCIONAL DEL PASO 1

A. Fundación del repositorio
Crear un monorepo con esta estructura:

/app_flutter
/backend_api
/infra
/docs
/scripts
/contracts

Detalle esperado:
- app_flutter: proyecto Flutter con estructura limpia, tema base y pantallas mínimas
- backend_api: FastAPI modular por dominios
- infra: docker compose, variables ejemplo, scripts de arranque
- docs: arquitectura, decisiones, modelo de datos, API y puesta en marcha
- scripts: seeds, utilitarios de desarrollo
- contracts: OpenAPI exportado, esquemas JSON o documentación de contratos

B. Docker Compose local mínimo
Implementar compose local con bajo consumo:
- postgres
- backend_api
Redis debe quedar preparado pero opcional, desactivado por defecto en este paso.

Requisitos:
- uso de .env
- healthchecks
- volúmenes persistentes
- parametrización de puertos
- perfiles de compose
- nada de latest
- sin credenciales hardcodeadas
- README para arranque local

C. Backend FastAPI
Construir backend modular por dominios:

1. auth
2. users
3. people
4. patients
5. professionals
6. verification
7. agreements
8. audit
9. access_control
10. files

Tecnologías sugeridas:
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- PostgreSQL con psycopg o asyncpg
- JWT access + refresh
- contraseña con Argon2 o bcrypt fuerte
- pytest

D. Frontend Flutter mínimo
No hacer una app completa. Solo un cascarón funcional para demostrar integración.
Pantallas mínimas:
- login
- registro de paciente
- registro de profesional
- pantalla básica según rol
- pantalla administrativa mínima de revisión de profesionales
- pantalla “acceso denegado”
- pantalla “perfil pendiente de verificación”

No se busca diseño final. Se busca demostrar flujo.

MODELO DE SEGURIDAD OBLIGATORIO

ROLES
- super_admin
- admin_validation
- admin_support
- patient
- professional

REGLAS
1. super_admin administra plataforma pero NO puede leer datos clínicos por defecto.
2. admin_validation puede revisar documentos de profesionales y aprobar/rechazar perfiles.
3. admin_support puede ver datos no clínicos de soporte.
4. patient gestiona su propia cuenta.
5. professional gestiona su perfil y documentos.
6. No debe existir ningún endpoint que devuelva datos clínicos por defecto a administradores.
7. Debe existir desde ahora la estructura para “acceso excepcional auditado”, aunque todavía no haya módulo clínico completo.

CONTROL CONTEXTUAL
Además del rol, el sistema debe verificar contexto:
- si el usuario es dueño del recurso
- si existe relación válida con el recurso
- si la acción es administrativa no clínica o clínica sensible
- si una acción requiere justificación
- si la acción debe generar auditoría reforzada

ENTIDADES Y TABLAS A IMPLEMENTAR EN EL PASO 1

Todas las tablas críticas deben incluir como mínimo:
- id UUID
- created_at
- updated_at
- deleted_at nullable
- created_by nullable
- updated_by nullable
- deleted_by nullable
- version integer
- status cuando aplique

1. users
Campos:
- id
- email unique
- password_hash
- is_email_verified
- status enum: pending_email_verification, active, suspended, soft_deleted
- last_login_at
- created_at
- updated_at
- deleted_at
- version

2. roles
Campos:
- id
- code unique
- name
- description
- is_system

3. user_roles
Campos:
- id
- user_id
- role_id
- assigned_at
- assigned_by
- revoked_at nullable
- revoked_by nullable
- status enum: active, revoked

4. people
Campos:
- id
- user_id unique
- first_name
- middle_name nullable
- last_name
- second_last_name nullable
- national_id
- phone
- birth_date nullable
- sex nullable
- country default Ecuador
- province nullable
- city nullable

5. patients
Campos:
- id
- user_id unique
- person_id unique
- verification_level enum: basic, identity_verified
- emergency_contact_name nullable
- emergency_contact_phone nullable
- status enum: active, restricted, suspended

6. professionals
Campos:
- id
- user_id unique
- person_id unique
- public_slug unique nullable
- professional_type
- public_display_name
- bio_public nullable
- years_experience nullable
- languages_json nullable
- onboarding_status enum: draft, submitted, under_review, approved, rejected, suspended
- is_public_profile_enabled boolean default false
- status enum: draft, pending_review, active, rejected, suspended

7. professional_credentials
Campos:
- id
- professional_id
- credential_type enum: title, license, specialty, course, other
- title
- issuing_entity
- credential_number nullable
- issue_date nullable
- expiry_date nullable
- verified_status enum: pending, approved, rejected
- notes nullable

8. professional_documents
Campos:
- id
- professional_id
- document_type enum: national_id_front, national_id_back, degree, registration_certificate, selfie_verification, cv, signed_agreement, supporting_document
- file_id
- original_filename
- mime_type
- sha256
- uploaded_at
- review_status enum: pending, approved, rejected
- review_notes nullable

9. agreements
Campos:
- id
- agreement_type enum: platform_terms, privacy_policy, professional_responsibility_agreement
- version_code
- title
- content_markdown
- is_active
- published_at

10. agreement_acceptances
Campos:
- id
- agreement_id
- user_id
- accepted_at
- acceptance_type enum: clickwrap, electronic_signature, equivalent_formal_mechanism
- ip_address
- user_agent
- evidence_file_id nullable
- status enum: accepted, revoked

11. verification_requests
Campos:
- id
- professional_id
- submitted_at
- assigned_admin_id nullable
- status enum: submitted, under_review, approved, rejected, needs_correction, suspended
- decision_at nullable
- decision_reason nullable
- reviewed_by nullable

12. verification_events
Campos:
- id
- verification_request_id
- event_type enum: submitted, assigned, comment_added, document_approved, document_rejected, approved, rejected, correction_requested, suspended
- event_payload_json
- created_at
- created_by

13. files
Campos:
- id
- storage_backend enum: local
- relative_path
- original_filename
- mime_type
- size_bytes
- sha256
- is_encrypted boolean
- access_level enum: public, private, sensitive
- owner_user_id nullable
- created_at
- deleted_at

14. file_permissions
Campos:
- id
- file_id
- subject_type enum: user, role
- subject_id
- permission enum: read, write, delete, grant
- granted_by
- expires_at nullable

15. audit_events
Campos:
- id
- occurred_at
- actor_user_id nullable
- actor_role_code nullable
- action
- entity_type
- entity_id
- request_id
- ip_address nullable
- user_agent nullable
- before_json nullable
- after_json nullable
- justification nullable
- severity enum: info, warning, critical

16. entity_versions
Tabla genérica o tablas de historial por entidad crítica.
Debe permitir reconstruir cambios de:
- users
- professionals
- professional_documents
- verification_requests
- agreements
- agreement_acceptances

17. exceptional_access_requests
Aunque todavía no haya módulo clínico completo, implementar la base de esta tabla para el futuro:
- id
- requester_user_id
- target_user_id nullable
- resource_type
- resource_id nullable
- reason
- patient_authorization_file_id nullable
- status enum: requested, approved, rejected, expired, revoked
- approved_by nullable
- approved_at nullable
- expires_at nullable

18. system_parameters
Campos:
- id
- key unique
- value_json
- description
- is_secret boolean

19. feature_flags
Campos:
- id
- code unique
- enabled
- description

SOFT DELETE Y VERSIONADO
Reglas obligatorias:
1. No eliminar físicamente registros críticos.
2. Usar deleted_at y deleted_by.
3. Incrementar version en cada cambio.
4. Registrar before_json y after_json en auditoría para cambios críticos.
5. Mantener historial de cambios de entidades críticas.
6. Todo cambio de estado debe quedar auditado.

MÁQUINAS DE ESTADO A IMPLEMENTAR EN ESTE PASO

1. user.status
pending_email_verification -> active -> suspended -> soft_deleted

2. professional.onboarding_status
draft -> submitted -> under_review -> approved
draft -> submitted -> under_review -> needs_correction -> submitted
draft -> submitted -> under_review -> rejected
approved -> suspended

3. verification_requests.status
submitted -> under_review -> approved
submitted -> under_review -> rejected
submitted -> under_review -> needs_correction -> submitted
approved -> suspended

4. agreement_acceptances.status
accepted -> revoked

ENDPOINTS REQUERIDOS

AUTH
- POST /api/v1/auth/register/patient
- POST /api/v1/auth/register/professional
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- GET /api/v1/auth/me

USERS / PROFILE
- GET /api/v1/users/me
- PATCH /api/v1/users/me
- GET /api/v1/patients/me
- PATCH /api/v1/patients/me
- GET /api/v1/professionals/me
- PATCH /api/v1/professionals/me

PROFESSIONAL DOCUMENTS
- POST /api/v1/professionals/me/documents
- GET /api/v1/professionals/me/documents
- DELETE /api/v1/professionals/me/documents/{id}   (soft delete)
- POST /api/v1/professionals/me/submit-verification

AGREEMENTS
- GET /api/v1/agreements/active
- POST /api/v1/agreements/{agreement_id}/accept

ADMIN VALIDATION
- GET /api/v1/admin/verification-requests
- GET /api/v1/admin/verification-requests/{id}
- POST /api/v1/admin/verification-requests/{id}/assign
- POST /api/v1/admin/verification-requests/{id}/request-correction
- POST /api/v1/admin/verification-requests/{id}/approve
- POST /api/v1/admin/verification-requests/{id}/reject
- GET /api/v1/admin/professionals/{id}
- GET /api/v1/admin/audit-events

EXCEPTIONAL ACCESS FOUNDATION
- POST /api/v1/access-exception-requests
- GET /api/v1/access-exception-requests/my-requests

REGLAS DE NEGOCIO IMPORTANTES

1. Un profesional no puede quedar público ni activo sin:
- usuario activo
- perfil mínimo completo
- documentos obligatorios cargados
- acuerdo aceptado
- solicitud de verificación aprobada

2. Un paciente sí puede registrarse con flujo más simple, pero no debe obtener privilegios administrativos ni clínicos ajenos.

3. Un administrador de validación puede revisar documentos profesionales, pero no debe existir ningún endpoint clínico accesible para ese rol.

4. Cada aprobación, rechazo, corrección o suspensión debe:
- cambiar estado
- generar auditoría
- dejar trazabilidad de actor y motivo

5. Cada archivo sensible debe quedar con:
- hash sha256
- metadatos
- permisos
- clasificación de acceso

6. Debe existir una capa de autorización reusable:
- require_role(...)
- require_owner_or_role(...)
- require_contextual_access(...)
- require_non_clinical_admin_scope(...)

7. Debe existir middleware o mecanismo equivalente para auditoría de operaciones críticas.

8. Debe existir request_id por petición.

9. Debe existir documentación clara de cómo en el futuro se impedirá el acceso clínico administrativo salvo acceso excepcional auditado.

ARCHIVOS Y ALMACENAMIENTO
En este paso se debe usar almacenamiento local estructurado.
Requisitos:
- path configurable por .env
- subdirectorios por tipo de documento
- nombre interno no basado solo en nombre original
- hash calculado al guardar
- validación de extensión y mime
- tamaño máximo configurable
- helper para reemplazo lógico, nunca borrado físico directo de archivos críticos

PRUEBAS AUTOMÁTICAS OBLIGATORIAS

Pruebas unitarias y de integración mínimas para:
1. registro de paciente
2. registro de profesional
3. login y refresh token
4. aceptación de acuerdo
5. carga de documento profesional
6. envío de solicitud de verificación
7. aprobación administrativa
8. rechazo administrativo
9. soft delete de documento
10. auditoría generada al aprobar o rechazar
11. bloqueo de acceso cuando un rol no autorizado intenta ver recursos ajenos
12. bloqueo de acceso administrativo a recurso sensible definido como clínico futuro
13. transición inválida de estados
14. control de concurrencia básica con version o updated_at

CASOS DE PRUEBA CLAVE
- un patient no puede acceder a endpoints admin
- un professional no puede aprobarse a sí mismo
- un admin_validation sí puede revisar verificación
- un admin_validation no puede leer datos clínicos
- un professional no aprobado no puede quedar público
- toda acción crítica genera audit_event
- soft delete no elimina físicamente la fila
- cambios incrementan version

ENTREGABLES OBLIGATORIOS
1. Código backend funcional
2. Código Flutter mínimo funcional
3. docker-compose.yml
4. .env.example
5. migraciones Alembic
6. seeds iniciales de roles, agreements y feature flags
7. colección de endpoints documentados
8. README de arranque local
9. documento corto de arquitectura
10. documento del modelo de datos del paso 1
11. documento de reglas de autorización
12. pruebas automáticas ejecutables

CRITERIOS DE ACEPTACIÓN
Se considerará terminado cuando:
- docker compose local levante correctamente
- PostgreSQL quede inicializado
- migraciones corran sin error
- API responda
- Flutter pueda autenticarse contra la API
- se pueda registrar paciente
- se pueda registrar profesional
- se puedan subir documentos del profesional
- se pueda enviar una solicitud de verificación
- un admin pueda aprobar o rechazar
- el estado del profesional cambie correctamente
- la auditoría registre eventos críticos
- no exista acceso administrativo clínico abierto
- las pruebas pasen

ESTÁNDARES DE IMPLEMENTACIÓN
- código limpio y modular
- nombres explícitos
- DTOs separados de modelos ORM
- repositorios/servicios donde aporte claridad
- validaciones de entrada
- manejo consistente de errores
- respuestas API homogéneas
- tipado
- comentarios solo donde realmente aporten
- evitar sobreingeniería

SALIDA ESPERADA DEL MODELO
El modelo debe entregar:
1. árbol de carpetas propuesto
2. explicación breve de decisiones
3. código del backend
4. código Flutter mínimo
5. docker compose
6. migraciones
7. seeds
8. pruebas
9. README
10. notas de lo que quedó preparado para el paso 2

INSTRUCCIÓN FINAL
Construir el paso 1 completo siguiendo exactamente este alcance. No desviarse a pagos, agenda avanzada, clínica completa ni teleconsulta real. Priorizar seguridad, trazabilidad, reversibilidad, claridad y posibilidad de crecimiento ordenado.
```

Se recomienda entregarle exactamente ese bloque al otro modelo.

Si se desea continuar de manera secuencial, el **paso 2** debería ser **perfiles públicos + buscador + disponibilidad + agenda base de citas**, apoyado sobre esta fundación.
