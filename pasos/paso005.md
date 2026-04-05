Se deja el **paso 5 masticado** para OpenCode: **órdenes de examen + resultados + laboratorios**, alineado con la decisión de manejar solicitudes de exámenes, carga de resultados y laboratorios como tercer tipo de cliente dentro de la plataforma. 

```text id="58214"
IMPLEMENTAR PASO 5 DEL MARKETPLACE DE SALUD.

CONTEXTO FIJO
- Stack: Flutter + FastAPI + PostgreSQL + Docker Compose.
- Paso 1 ya existe: auth, roles, users, patients, professionals, verification, agreements, audit.
- Paso 2 ya existe: perfiles públicos, disponibilidades, citas.
- Paso 3 ya existe: pagos y comisión de citas.
- Paso 4 ya existe: teleconsulta básica, nota clínica simple, receta, indicaciones, archivos clínicos.
- No cambiar arquitectura.
- Mantener soft delete, auditoría, versionado, estados y reversibilidad.
- Admin NO puede ver datos clínicos por defecto.
- La plataforma sigue siendo intermediario tecnológico.

OBJETIVO
Implementar:
1. órdenes de examen ligadas a una cita
2. catálogo base de exámenes
3. laboratorios y sucursales como tercer tipo de cliente
4. selección o derivación controlada de laboratorio
5. aceptación operativa de la orden por laboratorio
6. carga de resultados
7. publicación/liberación de resultados
8. acceso seguro de paciente y profesional a resultados
9. auditoría reforzada sobre acceso a resultados
10. pantallas Flutter mínimas

NO IMPLEMENTAR
- LIS completo
- integración HL7/FHIR
- conexión con equipos de laboratorio
- PACS/DICOM
- interpretación automática por IA
- facturación electrónica de laboratorios
- split de pagos a laboratorio
- órdenes hospitalarias complejas
- biometría
- resultados estructurados muy avanzados con reglas clínicas complejas
- flujo domiciliario de toma de muestras

ENFOQUE
Implementar primero un flujo documental y operativo controlado:
- el profesional genera la orden
- el paciente selecciona laboratorio o se deriva a uno
- el laboratorio acepta la orden
- el laboratorio sube resultados
- el laboratorio libera resultados
- el paciente y el profesional autorizado ven lo liberado

REGLAS DE NEGOCIO
1. Solo un professional autorizado de la cita puede emitir una orden de examen.
2. La orden de examen debe estar asociada a una cita existente.
3. La orden puede existir para cita presencial o teleconsulta.
4. Solo patient de la cita y professional de la cita pueden ver la orden completa.
5. El laboratorio solo puede ver datos mínimos necesarios para procesar la orden.
6. Admin no puede ver resultados clínicos por endpoints normales.
7. Todo acceso a resultados debe quedar auditado.
8. Toda modificación relevante de orden o resultado debe dejar historial.
9. Una orden no puede liberarse sin al menos un resultado cargado.
10. El paciente no puede modificar órdenes ni resultados.
11. El laboratorio no puede modificar la nota clínica ni la receta.
12. El professional puede ver resultados liberados de órdenes que él emitió.
13. Los resultados pueden existir como PDF, imagen y resumen de texto simple.
14. Los resultados liberados son visibles al paciente.
15. Los resultados draft no son visibles al paciente.
16. No borrar físicamente resultados críticos.
17. Si un resultado requiere corrección, debe quedar nueva versión o estado amended.
18. El laboratorio no debe recibir más datos del paciente que los necesarios para atender la orden.
19. El ranking de laboratorios en esta fase debe ser simple y transparente, sin publicidad disfrazada.
20. No implementar patrocinados en este paso.

ROLES NUEVOS
Agregar:
- laboratory_admin
- laboratory_operator

REGLAS DE ROLES
- laboratory_admin administra su laboratorio, sucursales, catálogo y órdenes asignadas
- laboratory_operator puede gestionar órdenes y resultados del laboratorio asignado
- ninguno puede ver información clínica ajena fuera de órdenes asignadas

TABLAS NUEVAS

1) laboratories
- id uuid pk
- legal_name varchar not null
- commercial_name varchar not null
- ruc varchar null
- status varchar not null   # draft, pending_review, active, suspended, rejected
- verification_status varchar not null   # pending, approved, rejected
- contact_email varchar null
- contact_phone varchar null
- created_at
- updated_at
- deleted_at null
- version int default 1

2) laboratory_public_profiles
- id uuid pk
- laboratory_id fk unique not null
- public_slug varchar unique not null
- public_description text null
- province varchar null
- city varchar null
- sector varchar null
- address_reference text null
- turnaround_hours int null
- accepts_digital_orders boolean default true
- is_public boolean default false
- created_at
- updated_at
- deleted_at null
- version int default 1

3) laboratory_branches
- id uuid pk
- laboratory_id fk not null
- branch_name varchar not null
- province varchar null
- city varchar null
- sector varchar null
- address_line text null
- phone varchar null
- email varchar null
- status varchar not null   # active, inactive
- created_at
- updated_at
- deleted_at null
- version int default 1

4) laboratory_user_memberships
- id uuid pk
- laboratory_id fk not null
- branch_id fk null
- user_id fk not null
- role_code varchar not null   # laboratory_admin, laboratory_operator
- status varchar not null   # active, revoked
- assigned_at
- revoked_at null
- created_at
- updated_at
- deleted_at null
- version int default 1

5) exam_catalog_master
- id uuid pk
- code varchar unique not null
- category varchar null
- name varchar not null
- description text null
- specimen_type varchar null
- is_active boolean default true
- created_at
- updated_at
- deleted_at null
- version int default 1

6) laboratory_exam_offers
- id uuid pk
- laboratory_id fk not null
- branch_id fk null
- exam_catalog_id fk not null
- internal_code varchar null
- price_amount numeric(10,2) null
- currency_code varchar(3) default 'USD'
- turnaround_hours int null
- is_active boolean default true
- created_at
- updated_at
- deleted_at null
- version int default 1
- unique(laboratory_id, branch_id, exam_catalog_id)

7) exam_orders
- id uuid pk
- appointment_id fk not null
- professional_id fk not null
- patient_id fk not null
- status varchar not null   # draft, issued, lab_selected, accepted_by_lab, partially_resulted, released, cancelled
- order_reason text null
- clinical_context_min text null
- preferred_laboratory_id fk null
- selected_laboratory_id fk null
- selected_branch_id fk null
- issued_at timestamptz null
- released_at timestamptz null
- created_at
- updated_at
- deleted_at null
- version int default 1

8) exam_order_items
- id uuid pk
- exam_order_id fk not null
- exam_catalog_id fk not null
- status varchar not null   # ordered, accepted, processing, result_uploaded, released, cancelled
- notes text null
- created_at
- updated_at
- deleted_at null
- version int default 1

9) exam_order_assignments
- id uuid pk
- exam_order_id fk unique not null
- laboratory_id fk not null
- branch_id fk null
- assigned_by_user_id fk not null
- assignment_source varchar not null   # patient_selected, professional_preferred, admin_assisted
- status varchar not null   # pending_acceptance, accepted, rejected, cancelled
- assigned_at timestamptz not null
- responded_at timestamptz null
- rejection_reason varchar null
- created_at
- updated_at
- deleted_at null
- version int default 1

10) exam_results
- id uuid pk
- exam_order_item_id fk unique not null
- exam_order_id fk not null
- patient_id fk not null
- laboratory_id fk not null
- branch_id fk null
- result_status varchar not null   # draft, released, amended, revoked
- summary_text text null
- observations text null
- result_data_json jsonb null
- released_at timestamptz null
- created_by_user_id fk not null
- created_at
- updated_at
- deleted_at null
- version int default 1

11) exam_result_versions
- id uuid pk
- exam_result_id fk not null
- version_number int not null
- snapshot_json jsonb not null
- changed_by_user_id fk not null
- change_reason varchar null
- created_at

12) exam_result_files
- id uuid pk
- exam_result_id fk not null
- file_id fk not null
- file_type varchar not null   # pdf, image, annex
- is_primary boolean default false
- created_at
- updated_at
- deleted_at null
- version int default 1

13) exam_access_audit
- id uuid pk
- resource_type varchar not null   # exam_order, exam_result, exam_result_file
- resource_id uuid not null
- exam_order_id fk null
- actor_user_id fk not null
- actor_role_code varchar not null
- action varchar not null   # create, read, update, release, amend, list, assign, accept
- justification varchar null
- request_id varchar null
- created_at

CAMBIOS A TABLAS EXISTENTES

appointments
agregar:
- has_exam_orders boolean default false

professional_public_profiles
sin cambios obligatorios

files
reutilizar storage existente con access_level = sensitive para resultados

MÁQUINAS DE ESTADO

exam_orders.status
- draft
- issued
- lab_selected
- accepted_by_lab
- partially_resulted
- released
- cancelled

Transiciones:
- draft -> issued
- issued -> lab_selected
- lab_selected -> accepted_by_lab
- accepted_by_lab -> partially_resulted
- partially_resulted -> released
- issued -> cancelled
- lab_selected -> cancelled
- accepted_by_lab -> cancelled

exam_order_items.status
- ordered
- accepted
- processing
- result_uploaded
- released
- cancelled

Transiciones:
- ordered -> accepted
- accepted -> processing
- processing -> result_uploaded
- result_uploaded -> released
- ordered -> cancelled
- accepted -> cancelled
- processing -> cancelled

exam_order_assignments.status
- pending_acceptance
- accepted
- rejected
- cancelled

Transiciones:
- pending_acceptance -> accepted
- pending_acceptance -> rejected
- pending_acceptance -> cancelled

exam_results.result_status
- draft
- released
- amended
- revoked

Transiciones:
- draft -> released
- released -> amended
- released -> revoked
- amended -> released

REGLAS DE MINIMIZACIÓN DE DATOS PARA LABORATORIOS
El laboratorio asignado solo puede ver:
- nombre del paciente
- identificador necesario
- sexo y fecha de nacimiento solo si realmente se requiere
- examen solicitado
- contexto clínico mínimo
- professional emisor
- sucursal asignada
- estado operativo
No puede ver:
- nota clínica completa
- private_professional_note
- receta
- indicaciones no relacionadas
- otros archivos clínicos de la cita

REGLAS DE ACCESO
1. patient solo puede leer sus órdenes y resultados propios.
2. professional solo puede crear órdenes y leer resultados de órdenes emitidas por él o ligadas a su cita.
3. laboratory_admin y laboratory_operator solo pueden ver órdenes asignadas a su laboratorio.
4. admin no puede leer contenido clínico por endpoints normales.
5. todo endpoint de órdenes/resultados debe usar require_exam_relationship().
6. todo READ de orden o resultado debe insertar exam_access_audit.
7. todo WRITE relevante debe insertar exam_access_audit y audit_event.
8. resultados draft no visibles al paciente.
9. resultados released sí visibles al paciente y professional autorizado.
10. si hay amended, debe mantenerse historial.

ENDPOINTS NUEVOS

PUBLIC
- GET /api/v1/public/laboratories
- GET /api/v1/public/laboratories/{public_slug}
- GET /api/v1/public/exam-catalog
- GET /api/v1/public/exam-catalog/search?q=
- GET /api/v1/patient/exam-orders/{id}/laboratory-options

PROFESSIONAL
- POST /api/v1/professionals/me/appointments/{id}/exam-orders
- GET /api/v1/professionals/me/appointments/{id}/exam-orders
- GET /api/v1/professionals/me/exam-orders/{order_id}
- PUT /api/v1/professionals/me/exam-orders/{order_id}
- POST /api/v1/professionals/me/exam-orders/{order_id}/issue
- POST /api/v1/professionals/me/exam-orders/{order_id}/cancel
- GET /api/v1/professionals/me/exam-orders/{order_id}/results

PATIENT
- GET /api/v1/patient/exam-orders
- GET /api/v1/patient/exam-orders/{order_id}
- POST /api/v1/patient/exam-orders/{order_id}/select-laboratory
- GET /api/v1/patient/exam-orders/{order_id}/results
- GET /api/v1/patient/exam-results/{result_id}
- GET /api/v1/patient/exam-results/{result_id}/files/{file_id}

LABORATORY
- GET /api/v1/laboratories/me/profile
- PUT /api/v1/laboratories/me/profile
- GET /api/v1/laboratories/me/branches
- POST /api/v1/laboratories/me/branches
- PUT /api/v1/laboratories/me/branches/{id}
- GET /api/v1/laboratories/me/exam-offers
- PUT /api/v1/laboratories/me/exam-offers
- GET /api/v1/laboratories/me/exam-orders
- GET /api/v1/laboratories/me/exam-orders/{order_id}
- POST /api/v1/laboratories/me/exam-orders/{order_id}/accept
- POST /api/v1/laboratories/me/exam-orders/{order_id}/reject
- POST /api/v1/laboratories/me/exam-order-items/{item_id}/start-processing
- POST /api/v1/laboratories/me/exam-order-items/{item_id}/results
- PUT /api/v1/laboratories/me/exam-results/{result_id}
- POST /api/v1/laboratories/me/exam-results/{result_id}/release
- POST /api/v1/laboratories/me/exam-results/{result_id}/amend
- POST /api/v1/laboratories/me/exam-results/{result_id}/revoke

ADMIN OPERATIVO
- GET /api/v1/admin/laboratories
- GET /api/v1/admin/laboratories/{id}
- POST /api/v1/admin/laboratories/{id}/approve
- POST /api/v1/admin/laboratories/{id}/reject
- POST /api/v1/admin/laboratories/{id}/suspend
- GET /api/v1/admin/exam-access-audit?order_id={id}
- GET /api/v1/admin/exam-orders/{id}/meta

NOTA:
Los endpoints admin solo exponen metadatos, estados, trazabilidad y auditoría. No contenido clínico completo.

REQUEST/RESPONSE CLAVES

POST /professionals/me/appointments/{id}/exam-orders
input:
- order_reason
- clinical_context_min
- preferred_laboratory_id optional
- items[]:
  - exam_catalog_id
  - notes optional
output:
- exam_order_id
- status
- items_count

POST /patient/exam-orders/{order_id}/select-laboratory
input:
- laboratory_id
- branch_id optional
output:
- assignment_id
- status
- selected_laboratory_id

POST /laboratories/me/exam-order-items/{item_id}/results
input:
- summary_text
- observations
- result_data_json optional
- files[] optional
output:
- exam_result_id
- result_status
- version

POST /laboratories/me/exam-results/{result_id}/release
output:
- exam_result_id
- result_status
- released_at

GET /patient/exam-orders/{order_id}/results
output:
- order_id
- order_status
- items[]:
  - order_item_id
  - exam_name
  - result_status
  - released_at

RANKING SIMPLE DE LABORATORIOS
Para GET /patient/exam-orders/{id}/laboratory-options:
ordenar por:
1. laboratorio activo y público
2. sucursal en misma ciudad
3. oferta activa para todos los exámenes pedidos
4. turnaround_hours asc
5. price_amount asc cuando exista
No implementar patrocinados ni publicidad.

VALIDACIONES
1. appointment debe existir.
2. professional autenticado debe ser dueño de la cita.
3. patient autenticado debe ser dueño de la orden.
4. no emitir orden vacía.
5. no aceptar laboratorio suspendido.
6. no aceptar selección de laboratorio no público o no activo.
7. no permitir upload de resultado sin assignment accepted.
8. no permitir release de resultado sin archivo o contenido mínimo.
9. no permitir patient ver draft.
10. no permitir laboratory editar orden clínica emitida por professional.
11. no permitir professional alterar resultado del laboratorio.
12. no permitir admin leer contenido de result_data_json por endpoints normales.
13. si se hace amend, crear exam_result_versions.
14. si se cancela orden, no permitir nuevos resultados.

SERVICIOS
1. exam catalog service
2. exam order service
3. laboratory selection service
4. laboratory assignment service
5. exam result service con versionado
6. exam result release service
7. exam authorization service
8. exam audit service

AUDITORÍA OBLIGATORIA
Registrar audit_event y/o exam_access_audit en:
- crear orden
- emitir orden
- cancelar orden
- seleccionar laboratorio
- aceptar/rechazar assignment
- iniciar procesamiento
- crear/editar resultado
- liberar resultado
- corregir resultado
- leer orden
- leer resultado
- descargar archivo de resultado

ARCHIVOS
- usar storage local existente
- access_level = sensitive
- sha256 obligatorio
- tamaño máximo configurable
- validación mime/extensión
- file permissions por relación clínica/laboratorio
- PDF e imágenes permitidas en esta fase

PRUEBAS AUTOMÁTICAS
1. professional puede crear orden con items válidos
2. no se puede emitir orden vacía
3. patient puede seleccionar laboratorio activo
4. no se puede seleccionar laboratorio inactivo
5. laboratorio asignado puede aceptar orden
6. laboratorio no asignado no puede ver orden
7. laboratory operator puede subir resultado draft
8. patient no ve resultado draft
9. patient sí ve resultado released
10. professional emisor sí ve resultado released
11. admin no ve contenido clínico del resultado
12. exam_access_audit se registra en lecturas
13. audit_event se registra en escrituras
14. amend crea versión
15. cancelación de orden bloquea nuevos resultados
16. ranking simple de laboratory-options funciona
17. minimización de datos para laboratorio se respeta

PANTALLAS FLUTTER MÍNIMAS

PATIENT
1. listado de órdenes de examen
2. detalle de orden
3. selección de laboratorio
4. estado de procesamiento
5. listado de resultados
6. ver/descargar resultado liberado

PROFESSIONAL
1. crear orden de examen desde cita
2. listar órdenes por cita
3. ver resultados liberados

LABORATORY
1. editar perfil público básico
2. gestionar sucursales
3. gestionar oferta de exámenes
4. listar órdenes asignadas
5. aceptar/rechazar orden
6. cargar resultado
7. liberar resultado
8. corregir resultado

ADMIN
1. listar laboratorios
2. aprobar/rechazar/suspender laboratorio
3. ver metadatos de órdenes/resultados
4. ver auditoría de acceso a órdenes/resultados
5. sin vista de contenido clínico completo

NO HACER UI COMPLEJA
- diseño simple
- loading/error/empty
- cliente HTTP limpio
- sin optimización prematura

SEEDS
- feature_flag laboratories_enabled=true
- feature_flag exam_orders_enabled=true
- feature_flag exam_results_enabled=true
- feature_flag laboratory_public_profiles_enabled=true
- exam_catalog_master con ejemplos básicos:
  - BH
  - GLUCOSA
  - PERFIL_LIPIDICO
  - TGO
  - TGP
  - TSH
  - EGO

ORDEN EXACTO DE IMPLEMENTACIÓN
1. migraciones
2. seeds
3. modelos ORM
4. schemas
5. autorización reusable de órdenes/resultados
6. exam catalog service
7. exam order service
8. laboratory selection/assignment service
9. exam result service con versionado
10. release/amend service
11. endpoints
12. tests backend
13. pantallas Flutter
14. integración Flutter-API
15. README paso 5

CRITERIOS DE ACEPTACIÓN
- professional puede emitir orden con varios exámenes
- patient puede seleccionar laboratorio
- laboratorio asignado puede aceptar y cargar resultados
- patient y professional autorizado pueden ver resultados liberados
- admin no ve contenido clínico
- accesos y cambios quedan auditados
- versionado de resultados corregidos funciona
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

```text id="27163"
Implementar paso 5:
órdenes de examen + laboratorios + carga y liberación de resultados.

Base existente:
FastAPI + PostgreSQL + Flutter.
Pasos 1 a 4 ya existen.

No implementar:
LIS, HL7/FHIR, equipos de laboratorio, PACS/DICOM, facturación lab, IA clínica.

Agregar roles:
- laboratory_admin
- laboratory_operator

Crear tablas:
laboratories
laboratory_public_profiles
laboratory_branches
laboratory_user_memberships
exam_catalog_master
laboratory_exam_offers
exam_orders
exam_order_items
exam_order_assignments
exam_results
exam_result_versions
exam_result_files
exam_access_audit

Agregar a appointments:
has_exam_orders boolean default false

Reglas:
- professional de la cita crea la orden
- patient selecciona laboratorio
- laboratorio asignado acepta
- laboratorio sube resultado draft
- laboratorio libera resultado
- patient y professional autorizado ven released
- admin no ve contenido clínico
- laboratorio ve solo contexto mínimo, no nota clínica completa
- toda lectura y escritura auditable
- cambios de resultado versionados

Estados:
exam_orders = draft, issued, lab_selected, accepted_by_lab, partially_resulted, released, cancelled
exam_order_items = ordered, accepted, processing, result_uploaded, released, cancelled
exam_results = draft, released, amended, revoked

Endpoints:
GET /public/laboratories
GET /public/laboratories/{slug}
GET /public/exam-catalog
GET /patient/exam-orders/{id}/laboratory-options

POST /professionals/me/appointments/{id}/exam-orders
GET /professionals/me/appointments/{id}/exam-orders
GET /professionals/me/exam-orders/{id}
PUT /professionals/me/exam-orders/{id}
POST /professionals/me/exam-orders/{id}/issue
POST /professionals/me/exam-orders/{id}/cancel
GET /professionals/me/exam-orders/{id}/results

GET /patient/exam-orders
GET /patient/exam-orders/{id}
POST /patient/exam-orders/{id}/select-laboratory
GET /patient/exam-orders/{id}/results
GET /patient/exam-results/{id}
GET /patient/exam-results/{id}/files/{file_id}

GET /laboratories/me/profile
PUT /laboratories/me/profile
CRUD /laboratories/me/branches
GET/PUT /laboratories/me/exam-offers
GET /laboratories/me/exam-orders
GET /laboratories/me/exam-orders/{id}
POST /laboratories/me/exam-orders/{id}/accept
POST /laboratories/me/exam-orders/{id}/reject
POST /laboratories/me/exam-order-items/{id}/start-processing
POST /laboratories/me/exam-order-items/{id}/results
PUT /laboratories/me/exam-results/{id}
POST /laboratories/me/exam-results/{id}/release
POST /laboratories/me/exam-results/{id}/amend
POST /laboratories/me/exam-results/{id}/revoke

GET /admin/laboratories
GET /admin/laboratories/{id}
POST /admin/laboratories/{id}/approve
POST /admin/laboratories/{id}/reject
POST /admin/laboratories/{id}/suspend
GET /admin/exam-access-audit?order_id={id}

Tests:
- no orden vacía
- patient selecciona laboratorio activo
- laboratorio no asignado no accede
- draft no visible al patient
- released visible al patient y professional
- admin no ve contenido clínico
- auditoría funciona
- versionado de amend funciona

Entregar código, migraciones, tests, Flutter mínimo y README.
```

Luego correspondería el **paso 6**: **calificaciones verificadas + comentarios + denuncias + moderación y suspensión de perfiles**.
