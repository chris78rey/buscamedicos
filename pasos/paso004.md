Se deja el **paso 4 masticado** para OpenCode: **teleconsulta básica + receta + indicaciones simples**, alineado con el proyecto ya definido de marketplace de salud, teleconsulta inicial, módulo básico de recetas e indicaciones y restricción fuerte para administradores sobre datos clínicos. 

```text id="51428"
IMPLEMENTAR PASO 4 DEL MARKETPLACE DE SALUD.

CONTEXTO FIJO
- Stack: Flutter + FastAPI + PostgreSQL + Docker Compose.
- Paso 1 ya existe: auth, roles, users, patients, professionals, verification, agreements, audit.
- Paso 2 ya existe: perfiles públicos, disponibilidades, slots, citas.
- Paso 3 ya existe: pagos, comisión, confirmación económica.
- No cambiar arquitectura.
- Mantener soft delete, auditoría, versionado, estados y reversibilidad.
- Admin NO puede ver datos clínicos por defecto.
- La plataforma sigue siendo intermediario tecnológico.

OBJETIVO
Implementar:
1. teleconsulta básica ligada a una cita pagada
2. enlace externo de videollamada
3. control de inicio y cierre de teleconsulta
4. nota clínica simple de atención
5. receta digital básica
6. indicaciones para el paciente
7. archivos clínicos simples por cita
8. control de acceso clínico estricto
9. auditoría reforzada sobre acceso clínico
10. pantallas Flutter mínimas

NO IMPLEMENTAR
- historia clínica completa
- módulo hospitalario
- interoperabilidad HL7/FHIR
- firma electrónica avanzada de receta
- farmacia
- laboratorio
- diagnósticos complejos codificados
- telemedicina a domicilio
- videollamada propia compleja
- chat clínico
- dictado por voz
- IA clínica

ENFOQUE
Implementar teleconsulta básica usando enlace externo o proveedor externo simple.
No construir motor propio de videollamada.
Solo guardar referencia, estado y auditoría del uso.

REGLAS DE NEGOCIO
1. Solo citas con financial_status = paid pueden habilitar teleconsulta.
2. Solo citas con modality_code = teleconsulta aplican a este paso.
3. La teleconsulta debe estar asociada a una cita existente.
4. Solo el paciente de la cita y el profesional de la cita pueden ver el contenido clínico.
5. Admin no puede ver nota clínica, receta ni indicaciones por defecto.
6. Todo acceso a recurso clínico debe generar auditoría reforzada.
7. La receta de este paso es básica, no sustituye flujos regulatorios complejos.
8. La nota clínica simple no equivale a historia clínica completa.
9. Solo el profesional de la cita puede crear o editar contenido clínico.
10. El paciente puede leer receta, indicaciones y documentos autorizados de su propia cita.
11. No borrar físicamente contenido clínico crítico.
12. Toda corrección clínica debe dejar versión e historial.
13. Debe existir base para acceso excepcional auditado, pero no habilitar acceso libre.
14. Una teleconsulta no puede marcarse completed si nunca inició.
15. El paciente no puede editar receta ni nota clínica.

TABLAS NUEVAS

1) teleconsultation_sessions
- id uuid pk
- appointment_id fk unique not null
- provider_code varchar not null   # external_link, jitsi, meet, zoom, other
- session_url text not null
- host_url text null
- access_code varchar null
- scheduled_start timestamptz not null
- scheduled_end timestamptz not null
- actual_start timestamptz null
- actual_end timestamptz null
- status varchar not null   # created, ready, in_progress, completed, cancelled, expired
- created_by_user_id fk not null
- created_at
- updated_at
- deleted_at null
- version int default 1

2) clinical_notes_simple
- id uuid pk
- appointment_id fk unique not null
- professional_id fk not null
- patient_id fk not null
- note_status varchar not null   # draft, signed_simple, amended
- reason_for_consultation text null
- subjective_summary text null
- objective_summary text null
- assessment text null
- plan text null
- private_professional_note text null
- visible_to_patient boolean default false
- created_at
- updated_at
- deleted_at null
- version int default 1

3) clinical_note_versions
- id uuid pk
- clinical_note_id fk not null
- version_number int not null
- snapshot_json jsonb not null
- changed_by_user_id fk not null
- change_reason varchar null
- created_at

4) prescriptions
- id uuid pk
- appointment_id fk not null
- professional_id fk not null
- patient_id fk not null
- status varchar not null   # draft, issued, revoked
- issued_at timestamptz null
- general_notes text null
- created_at
- updated_at
- deleted_at null
- version int default 1

5) prescription_items
- id uuid pk
- prescription_id fk not null
- medication_name varchar not null
- presentation varchar null
- dosage varchar not null
- frequency varchar not null
- duration varchar not null
- route varchar null
- instructions text null
- created_at
- updated_at
- deleted_at null
- version int default 1

6) care_instructions
- id uuid pk
- appointment_id fk unique not null
- professional_id fk not null
- patient_id fk not null
- status varchar not null   # draft, issued, amended
- content text not null
- follow_up_recommended boolean default false
- follow_up_note varchar null
- created_at
- updated_at
- deleted_at null
- version int default 1

7) clinical_files
- id uuid pk
- appointment_id fk not null
- uploaded_by_user_id fk not null
- file_id fk not null
- file_type varchar not null   # receta_pdf, indicacion_pdf, documento_clinico, imagen_clinica, otro
- is_visible_to_patient boolean default true
- status varchar not null default 'active'
- created_at
- updated_at
- deleted_at null
- version int default 1

8) clinical_access_audit
- id uuid pk
- resource_type varchar not null   # clinical_note, prescription, care_instruction, clinical_file, teleconsultation
- resource_id uuid not null
- appointment_id fk null
- actor_user_id fk not null
- actor_role_code varchar not null
- action varchar not null   # create, read, update, revoke, list, start_session, end_session
- justification varchar null
- request_id varchar null
- created_at

CAMBIOS A TABLAS EXISTENTES

appointments
agregar:
- consultation_status varchar not null default 'not_started'
Valores:
- not_started
- teleconsult_ready
- in_consultation
- completed
- cancelled

Opcional:
- has_clinical_content boolean default false

MÁQUINA DE ESTADOS TELECONSULTA

teleconsultation_sessions.status
- created
- ready
- in_progress
- completed
- cancelled
- expired

Transiciones:
- created -> ready
- ready -> in_progress
- ready -> cancelled
- ready -> expired
- in_progress -> completed
- in_progress -> cancelled

appointments.consultation_status
- not_started
- teleconsult_ready
- in_consultation
- completed
- cancelled

Transiciones:
- not_started -> teleconsult_ready
- teleconsult_ready -> in_consultation
- in_consultation -> completed
- teleconsult_ready -> cancelled
- in_consultation -> cancelled

prescriptions.status
- draft -> issued
- issued -> revoked

care_instructions.status
- draft -> issued
- issued -> amended

clinical_notes_simple.note_status
- draft -> signed_simple
- signed_simple -> amended

REGLAS DE ACCESO CLÍNICO
1. patient solo puede leer recursos clínicos de su propia cita.
2. professional solo puede crear/editar/leer recursos clínicos de citas asignadas a él.
3. admin no puede acceder a contenido clínico usando endpoints normales.
4. todo endpoint clínico debe pasar por require_clinical_relationship().
5. todo READ clínico debe insertar clinical_access_audit.
6. todo WRITE clínico debe insertar clinical_access_audit y audit_event.
7. private_professional_note nunca es visible al paciente.
8. visible_to_patient en nota clínica controla visibilidad parcial al paciente.
9. archivos clínicos deben respetar file permissions y clinical relationship.

ENDPOINTS NUEVOS

TELECONSULTA - PROFESSIONAL
- POST /api/v1/professionals/me/appointments/{id}/teleconsultation
- GET /api/v1/professionals/me/appointments/{id}/teleconsultation
- POST /api/v1/professionals/me/appointments/{id}/teleconsultation/start
- POST /api/v1/professionals/me/appointments/{id}/teleconsultation/end
- POST /api/v1/professionals/me/appointments/{id}/teleconsultation/cancel

TELECONSULTA - PATIENT
- GET /api/v1/patient/appointments/{id}/teleconsultation
- POST /api/v1/patient/appointments/{id}/teleconsultation/join-log

NOTA CLÍNICA SIMPLE
- GET /api/v1/professionals/me/appointments/{id}/clinical-note
- PUT /api/v1/professionals/me/appointments/{id}/clinical-note
- POST /api/v1/professionals/me/appointments/{id}/clinical-note/sign-simple
- GET /api/v1/patient/appointments/{id}/clinical-note

RECETAS
- GET /api/v1/professionals/me/appointments/{id}/prescription
- POST /api/v1/professionals/me/appointments/{id}/prescription
- PUT /api/v1/professionals/me/appointments/{id}/prescription/{prescription_id}
- POST /api/v1/professionals/me/appointments/{id}/prescription/{prescription_id}/issue
- POST /api/v1/professionals/me/appointments/{id}/prescription/{prescription_id}/revoke
- GET /api/v1/patient/appointments/{id}/prescription

INDICACIONES
- GET /api/v1/professionals/me/appointments/{id}/care-instructions
- PUT /api/v1/professionals/me/appointments/{id}/care-instructions
- POST /api/v1/professionals/me/appointments/{id}/care-instructions/issue
- GET /api/v1/patient/appointments/{id}/care-instructions

ARCHIVOS CLÍNICOS
- POST /api/v1/professionals/me/appointments/{id}/clinical-files
- GET /api/v1/professionals/me/appointments/{id}/clinical-files
- GET /api/v1/patient/appointments/{id}/clinical-files
- DELETE /api/v1/professionals/me/appointments/{id}/clinical-files/{file_id}

ADMIN OPERATIVO
- GET /api/v1/admin/appointments/{id}/teleconsultation-meta
- GET /api/v1/admin/clinical-access-audit?appointment_id={id}

NOTA:
Los endpoints admin solo deben exponer metadatos operativos y auditoría, nunca contenido clínico.

REQUEST/RESPONSE CLAVES

POST /professionals/me/appointments/{id}/teleconsultation
input:
- provider_code
- session_url
- host_url optional
- access_code optional
output:
- teleconsultation_session_id
- status
- scheduled_start
- scheduled_end

PUT /professionals/me/appointments/{id}/clinical-note
input:
- reason_for_consultation
- subjective_summary
- objective_summary
- assessment
- plan
- private_professional_note
- visible_to_patient
- change_reason
output:
- clinical_note_id
- note_status
- version

POST /professionals/me/appointments/{id}/prescription
input:
- general_notes
- items[]:
  - medication_name
  - presentation
  - dosage
  - frequency
  - duration
  - route
  - instructions
output:
- prescription_id
- status
- items_count

PUT /professionals/me/appointments/{id}/care-instructions
input:
- content
- follow_up_recommended
- follow_up_note
output:
- care_instruction_id
- status

GET /patient/appointments/{id}/clinical-note
output:
- appointment_id
- visible_to_patient
- reason_for_consultation
- subjective_summary
- objective_summary
- assessment
- plan
No incluir private_professional_note.

VALIDACIONES
1. cita debe existir
2. cita debe pertenecer al professional o patient autenticado
3. cita debe tener modality_code = teleconsulta para teleconsultation session
4. cita debe estar financial_status = paid
5. no crear teleconsultation para cita cancelada
6. no crear segunda sesión activa para la misma cita
7. no emitir receta vacía
8. no emitir indicaciones vacías
9. no completar teleconsulta sin actual_start
10. no permitir patient leer nota si visible_to_patient = false
11. no permitir admin leer private_professional_note
12. no permitir borrar lógico de receta issued sin dejar estado revoked

SERVICIOS
1. teleconsultation session service
2. clinical note service con versionado
3. prescription service
4. care instructions service
5. clinical file service
6. clinical authorization service
7. clinical audit service

AUDITORÍA OBLIGATORIA
Registrar audit_event y/o clinical_access_audit en:
- crear sesión de teleconsulta
- iniciar teleconsulta
- cerrar teleconsulta
- cancelar teleconsulta
- leer nota clínica
- crear/editar/firma simple de nota clínica
- crear/editar/emitir/revocar receta
- crear/editar/emitir indicaciones
- subir/listar/descargar archivo clínico

ARCHIVOS
- usar storage local existente
- access_level = sensitive
- sha256 obligatorio
- tamaño máximo configurable
- validación mime/extensión
- permisos por relación clínica

PRUEBAS AUTOMÁTICAS
1. no crear teleconsulta para cita unpaid
2. sí crear teleconsulta para cita paid y modalidad teleconsulta
3. professional puede iniciar y cerrar sesión
4. patient puede ver metadatos de su teleconsulta
5. patient no ve teleconsulta ajena
6. clinical note se crea y versiona
7. private_professional_note no se expone al paciente
8. patient no ve clinical note si visible_to_patient = false
9. prescription draft se puede emitir
10. prescription issued se puede revocar
11. care instructions se crean y emiten
12. admin no puede leer contenido clínico
13. clinical_access_audit se registra en lecturas clínicas
14. audit_event se registra en escrituras clínicas
15. delete lógico de archivo clínico funciona
16. transiciones inválidas fallan

PANTALLAS FLUTTER MÍNIMAS

PATIENT
1. detalle de cita teleconsulta
2. ver enlace/sala disponible
3. ver receta
4. ver indicaciones
5. ver archivos clínicos permitidos
6. ver nota clínica visible si corresponde

PROFESSIONAL
1. crear sesión de teleconsulta
2. iniciar/finalizar teleconsulta
3. editar nota clínica simple
4. crear/editar receta
5. emitir/revocar receta
6. crear/editar indicaciones
7. subir archivos clínicos

ADMIN
1. ver metadatos operativos de teleconsulta
2. ver auditoría de acceso clínico
3. sin vista de contenido clínico

NO HACER UI COMPLEJA
- diseño simple
- manejo loading/error/empty
- cliente HTTP limpio
- sin optimización prematura

SEEDS
- feature_flag teleconsultation_enabled=true
- feature_flag prescriptions_enabled=true
- feature_flag care_instructions_enabled=true
- feature_flag clinical_simple_notes_enabled=true

ORDEN EXACTO DE IMPLEMENTACIÓN
1. migraciones
2. seeds
3. modelos ORM
4. schemas
5. autorización clínica reusable
6. teleconsultation service
7. clinical notes service con versionado
8. prescription service
9. care instructions service
10. clinical files service
11. endpoints
12. tests backend
13. pantallas Flutter
14. integración Flutter-API
15. README paso 4

CRITERIOS DE ACEPTACIÓN
- cita pagada de teleconsulta puede tener sesión
- professional puede iniciar y cerrar teleconsulta
- professional puede registrar nota clínica simple
- professional puede emitir receta
- professional puede emitir indicaciones
- patient puede ver solo lo autorizado de su propia cita
- admin no ve contenido clínico
- auditoría clínica y general funciona
- versionado de nota clínica funciona
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

```text id="73624"
Implementar paso 4:
teleconsulta básica + nota clínica simple + receta + indicaciones + archivos clínicos.

Base existente:
FastAPI + PostgreSQL + Flutter.
Paso 1, 2 y 3 ya existen.

No implementar:
historia clínica completa, HL7/FHIR, laboratorio, videollamada propia compleja, IA clínica, domicilio.

Crear tablas:
teleconsultation_sessions
clinical_notes_simple
clinical_note_versions
prescriptions
prescription_items
care_instructions
clinical_files
clinical_access_audit

Agregar a appointments:
consultation_status = not_started|teleconsult_ready|in_consultation|completed|cancelled

Reglas:
- solo citas paid y modality teleconsulta pueden crear teleconsulta
- solo professional de la cita puede crear/editar contenido clínico
- patient solo lee contenido de su cita
- admin no puede leer contenido clínico
- toda lectura clínica auditable
- toda escritura clínica auditable
- private_professional_note nunca visible al patient

Endpoints:
POST /professionals/me/appointments/{id}/teleconsultation
GET /professionals/me/appointments/{id}/teleconsultation
POST /professionals/me/appointments/{id}/teleconsultation/start
POST /professionals/me/appointments/{id}/teleconsultation/end
POST /professionals/me/appointments/{id}/teleconsultation/cancel
GET /patient/appointments/{id}/teleconsultation

GET /professionals/me/appointments/{id}/clinical-note
PUT /professionals/me/appointments/{id}/clinical-note
POST /professionals/me/appointments/{id}/clinical-note/sign-simple
GET /patient/appointments/{id}/clinical-note

GET /professionals/me/appointments/{id}/prescription
POST /professionals/me/appointments/{id}/prescription
PUT /professionals/me/appointments/{id}/prescription/{id}
POST /professionals/me/appointments/{id}/prescription/{id}/issue
POST /professionals/me/appointments/{id}/prescription/{id}/revoke
GET /patient/appointments/{id}/prescription

GET /professionals/me/appointments/{id}/care-instructions
PUT /professionals/me/appointments/{id}/care-instructions
POST /professionals/me/appointments/{id}/care-instructions/issue
GET /patient/appointments/{id}/care-instructions

POST /professionals/me/appointments/{id}/clinical-files
GET /professionals/me/appointments/{id}/clinical-files
GET /patient/appointments/{id}/clinical-files
DELETE /professionals/me/appointments/{id}/clinical-files/{file_id}

GET /admin/appointments/{id}/teleconsultation-meta
GET /admin/clinical-access-audit?appointment_id={id}

Tests:
- no teleconsulta en cita unpaid
- sí teleconsulta en cita paid
- patient no ve recursos ajenos
- admin no ve contenido clínico
- nota clínica versiona
- private note no visible
- receta se emite
- indicaciones se emiten
- auditoría funciona

Entregar código, migraciones, tests, Flutter mínimo y README.
```

Luego tocaría el **paso 5**: **órdenes de examen + resultados + laboratorios**.
