Se deja el **paso 9** listo para OpenCode. Este paso mantiene la IA como **apoyo no clínico**, enfocada en búsqueda inteligente, resumen de perfiles, ayuda de redacción, clasificación operativa y soporte administrativo, sin diagnóstico ni decisiones clínicas automáticas, tal como quedó definido para el proyecto.  

```text
IMPLEMENTAR PASO 9 DEL MARKETPLACE DE SALUD.

CONTEXTO FIJO
- Stack: Flutter + FastAPI + PostgreSQL + Docker Compose.
- Pasos 1 a 8 ya existen.
- No cambiar arquitectura base.
- Mantener soft delete, auditoría, versionado, estados y reversibilidad.
- Admin NO puede ver datos clínicos por defecto.
- La plataforma sigue siendo intermediario tecnológico.
- La IA en este proyecto NO toma decisiones clínicas.
- La IA solo puede actuar como apoyo no clínico, asistente operativo y capa de búsqueda/resumen controlado.

OBJETIVO
Implementar:
1. búsqueda inteligente asistida para profesionales y laboratorios
2. resumen asistido de perfiles públicos
3. ayuda de redacción no clínica para profesionales
4. ayuda de redacción operativa para laboratorios y administración
5. clasificación asistida de tickets, reportes y denuncias
6. resumen administrativo de auditorías y trazabilidad
7. bitácora completa de prompts, respuestas, costos y uso
8. control de políticas de IA y límites por rol
9. pantallas Flutter mínimas para uso de IA
10. integración opcional con OpenRouter mediante adaptador desacoplado

NO IMPLEMENTAR
- diagnóstico automático
- triage clínico automático
- prescripción automática
- interpretación clínica automática de exámenes
- decisión médica automática
- chatbot clínico autónomo
- consejos médicos sin supervisión
- scoring de riesgo clínico
- moderación automática irreversible
- acciones automáticas críticas sin confirmación humana
- IA que lea clínico sensible sin políticas y permisos explícitos

ENFOQUE
Implementar una capa de IA segura, limitada y auditable:
- solo usa datos permitidos por política
- nunca responde como sustituto del professional
- toda salida importante requiere confirmación humana antes de persistirse
- todo uso queda auditado
- todo prompt sensible pasa por política de uso
- la IA puede sugerir, resumir, clasificar o redactar
- la IA no ejecuta acciones críticas por sí sola

CASOS DE USO INICIALES PERMITIDOS

1) BÚSQUEDA INTELIGENTE PÚBLICA
- convertir consulta libre del usuario en filtros estructurados
- ejemplo: “neurólogo en Quito con teleconsulta y experiencia en adultos mayores”
- la IA sugiere filtros, pero la búsqueda final sigue ejecutándose con PostgreSQL y reglas del sistema
- no inventar profesionales ni datos

2) RESUMEN DE PERFIL PÚBLICO
- resumir el perfil público de un professional o laboratorio
- usar solo campos públicos ya permitidos
- no usar documentos privados ni validaciones internas

3) AYUDA DE REDACCIÓN NO CLÍNICA PARA PROFESSIONAL
- redactar bio pública
- mejorar descripción de servicios
- ayudar a redactar mensajes operativos para el paciente
- ayudar a ordenar currículo público
- no redactar diagnósticos automáticos ni contenido clínico final sin revisión humana

4) AYUDA OPERATIVA PARA LABORATORIO
- mejorar descripciones de exámenes
- resumir instrucciones de preparación no clínica
- ordenar textos de atención al paciente

5) CLASIFICACIÓN ASISTIDA DE REPORTES Y DENUNCIAS
- sugerir categoría
- sugerir prioridad
- resumir evidencia textual
- nunca resolver automáticamente
- nunca sancionar automáticamente

6) RESUMEN DE AUDITORÍA Y ACCESOS
- resumir eventos operativos para admin autorizado
- nunca ocultar eventos reales
- solo resumir, no alterar evidencia

7) ASISTENTE INTERNO DE SOPORTE
- explicar estados del sistema
- sugerir siguiente acción operativa
- responder sobre reglas del flujo según documentación interna no sensible

ROLES QUE PUEDEN USAR IA
- patient: búsqueda inteligente pública y explicación de perfiles públicos
- professional: ayuda de redacción no clínica y resumen operativo de su propia actividad
- laboratory_admin / laboratory_operator: ayuda operativa y redacción no clínica
- admin_support / admin_moderation / admin_privacy / privacy_auditor: clasificación, resumen operativo y apoyo administrativo
- super_admin: igual que admin técnico, sin acceso libre a clínico
- ningún rol obtiene acceso clínico nuevo solo por usar IA

REGLAS DE NEGOCIO
1. La IA nunca debe presentarse como profesional de la salud.
2. La IA debe marcar sus salidas como sugerencia o borrador cuando corresponda.
3. Ninguna salida de IA puede persistirse automáticamente en campos críticos sin confirmación humana.
4. Todo uso de IA debe registrar actor, propósito, contexto permitido, costo y resultado.
5. La IA no debe recibir datos clínicos sensibles salvo caso futuro explícitamente habilitado por policy.
6. La IA debe operar por política de capacidad permitida por rol.
7. Debe existir apagado por feature flags.
8. Debe existir rate limit por usuario y por rol para IA.
9. Debe existir presupuesto y control básico de costo por rol o módulo.
10. La IA puede proponer filtros, resúmenes, etiquetas o borradores, pero no ejecutar sanciones, pagos, recetas ni diagnósticos.
11. Si una solicitud infringe política interna, debe ser rechazada y quedar auditada.
12. La IA no debe inventar hechos no presentes en el contexto permitido.
13. Las respuestas deben incluir metadatos mínimos de trazabilidad interna.
14. Los prompts y respuestas deben poder ocultar/redactar PII cuando aplique.
15. Debe existir política de retención para logs de IA.

TABLAS NUEVAS

1) ai_feature_policies
- id uuid pk
- feature_code varchar unique not null
- name varchar not null
- description text null
- is_active boolean default true
- allowed_roles_json jsonb not null
- allowed_resource_scopes_json jsonb not null
- requires_human_confirmation boolean default true
- max_input_chars int null
- max_output_chars int null
- max_requests_per_hour int null
- created_at
- updated_at
- deleted_at null
- version int default 1

2) ai_providers
- id uuid pk
- provider_code varchar unique not null
- name varchar not null
- is_active boolean default true
- base_url text null
- model_default varchar null
- created_at
- updated_at
- deleted_at null
- version int default 1

3) ai_models
- id uuid pk
- provider_id fk not null
- model_code varchar not null
- model_name varchar not null
- use_case varchar null
- is_active boolean default true
- input_cost_per_1k numeric(10,6) null
- output_cost_per_1k numeric(10,6) null
- context_limit int null
- created_at
- updated_at
- deleted_at null
- version int default 1
- unique(provider_id, model_code)

4) ai_prompts_catalog
- id uuid pk
- prompt_code varchar unique not null
- feature_code varchar not null
- title varchar not null
- system_prompt text not null
- template_text text not null
- is_active boolean default true
- created_at
- updated_at
- deleted_at null
- version int default 1

5) ai_interactions
- id uuid pk
- actor_user_id fk not null
- actor_role_code varchar not null
- feature_code varchar not null
- provider_code varchar not null
- model_code varchar not null
- input_scope varchar not null
- input_redacted boolean default true
- prompt_text_redacted text null
- raw_prompt_hash varchar null
- response_text_redacted text null
- response_status varchar not null
- rejection_reason varchar null
- token_input int null
- token_output int null
- estimated_cost numeric(10,6) null
- latency_ms int null
- request_id varchar null
- created_at
- updated_at
- deleted_at null
- version int default 1

6) ai_interaction_sources
- id uuid pk
- ai_interaction_id fk not null
- source_type varchar not null
- source_id uuid null
- source_scope varchar not null
- created_at
- updated_at
- deleted_at null
- version int default 1

7) ai_usage_quotas
- id uuid pk
- subject_type varchar not null
- subject_id uuid null
- role_code varchar null
- feature_code varchar not null
- period_code varchar not null
- max_requests int not null
- max_estimated_cost numeric(10,4) null
- is_active boolean default true
- created_at
- updated_at
- deleted_at null
- version int default 1

8) ai_usage_counters
- id uuid pk
- subject_type varchar not null
- subject_id uuid null
- role_code varchar null
- feature_code varchar not null
- period_code varchar not null
- period_start timestamptz not null
- request_count int not null default 0
- accumulated_cost numeric(10,4) not null default 0
- created_at
- updated_at
- deleted_at null
- version int default 1

9) ai_feedback
- id uuid pk
- ai_interaction_id fk not null
- actor_user_id fk not null
- rating smallint null
- was_used boolean null
- feedback_text text null
- created_at
- updated_at
- deleted_at null
- version int default 1

10) ai_guardrail_events
- id uuid pk
- actor_user_id fk null
- actor_role_code varchar null
- feature_code varchar not null
- event_type varchar not null
- details_json jsonb null
- request_id varchar null
- created_at
- updated_at
- deleted_at null
- version int default 1

FEATURE FLAGS
- ai_assistant_enabled
- ai_search_enabled
- ai_writing_enabled
- ai_moderation_assist_enabled
- ai_audit_summary_enabled

MÓDULOS NUEVOS
- backend_api/app/domains/ai_core
- backend_api/app/domains/ai_search
- backend_api/app/domains/ai_writing
- backend_api/app/domains/ai_moderation
- backend_api/app/domains/ai_audit

ARQUITECTURA DE IA
Implementar adaptador desacoplado:

AIProviderAdapter
- generate_text(feature_code, prompt, model_config, metadata) -> result

Implementaciones:
1. MockAIProviderAdapter
2. OpenRouterProviderAdapter

Servicios:
1. ai policy service
2. ai prompt builder service
3. ai quota service
4. ai interaction logger
5. ai guardrail service
6. ai search assistant service
7. ai profile summary service
8. ai writing assistant service
9. ai moderation classifier service
10. ai audit summarizer service

REGLAS DE GUARDRAILS
1. Si el input contiene clínico sensible y la feature no lo permite, bloquear.
2. Si el rol no está permitido en la feature, bloquear.
3. Si supera cuota o costo, bloquear.
4. Si intenta pedir diagnóstico, receta o interpretación médica, bloquear o redirigir.
5. Si el contexto solicitado no pertenece al actor, bloquear.
6. Si la salida contiene alucinación detectable por validación simple, marcar advertencia o rechazar persistencia.
7. Todo bloqueo genera ai_guardrail_event y ai_interaction con response_status correspondiente.
8. Para features críticas de redacción, la salida debe marcarse como borrador.

FEATURES A IMPLEMENTAR

1) search_assistant
Uso:
- patient o usuario público
Entrada:
- texto libre
Salida:
- filtros estructurados sugeridos:
  - specialty
  - city
  - modality
  - price_range
  - keywords_public
- luego ejecutar búsqueda real existente con esos filtros

2) profile_summary
Uso:
- patient, professional, admin autorizado
Entrada:
- professional_id o laboratory_id público
Salida:
- resumen breve del perfil público
Fuente:
- solo public profile y datos públicos visibles

3) writing_assistant
Uso:
- professional para bio pública
- laboratory para descripción pública
- admin para textos operativos
Entrada:
- texto base
- estilo deseado
Salida:
- borrador mejorado
Persistencia:
- solo después de confirmación humana

4) moderation_classifier
Uso:
- admin_moderation
Entrada:
- texto de report o denuncia
Salida:
- categoría sugerida
- prioridad sugerida
- resumen corto
- indicadores de riesgo textual
No resuelve ni sanciona automáticamente.

5) audit_summarizer
Uso:
- admin_privacy, privacy_auditor, super_admin técnico
Entrada:
- conjunto de audit_events o clinical_access_logs ya permitidos
Salida:
- resumen ejecutivo operativo
No modifica evidencia.

ENDPOINTS NUEVOS

PUBLIC / PATIENT
- POST /api/v1/ai/search-assistant
- GET /api/v1/ai/search-assistant/features
- POST /api/v1/ai/profile-summary/professional/{public_slug}
- POST /api/v1/ai/profile-summary/laboratory/{public_slug}
- GET /api/v1/ai/interactions/me
- POST /api/v1/ai/interactions/{id}/feedback

PROFESSIONAL
- POST /api/v1/professionals/me/ai/writing-assistant/profile-bio
- POST /api/v1/professionals/me/ai/writing-assistant/patient-message
- GET /api/v1/professionals/me/ai/interactions

LABORATORY
- POST /api/v1/laboratories/me/ai/writing-assistant/profile-description
- POST /api/v1/laboratories/me/ai/writing-assistant/preparation-text
- GET /api/v1/laboratories/me/ai/interactions

ADMIN MODERATION
- POST /api/v1/admin/moderation/ai/classify-report/{report_id}
- POST /api/v1/admin/moderation/ai/summarize-report/{report_id}

ADMIN PRIVACY / AUDITOR
- POST /api/v1/admin/privacy/ai/summarize-access-logs
- POST /api/v1/privacy-auditor/ai/summarize-access-logs

ADMIN IA
- GET /api/v1/admin/ai/providers
- GET /api/v1/admin/ai/models
- GET /api/v1/admin/ai/feature-policies
- PUT /api/v1/admin/ai/feature-policies/{feature_code}
- GET /api/v1/admin/ai/interactions
- GET /api/v1/admin/ai/guardrail-events
- GET /api/v1/admin/ai/usage
- GET /api/v1/admin/ai/quotas
- PUT /api/v1/admin/ai/quotas/{feature_code}

VALIDACIONES
1. feature flag global y por feature activos
2. rol permitido por ai_feature_policies
3. cuota no excedida
4. longitud máxima respetada
5. provider/model activos
6. profile_summary solo usa datos públicos
7. writing_assistant no persiste automáticamente
8. moderation_classifier solo accesible a admin_moderation
9. audit_summarizer solo usa logs ya accesibles al actor
10. no enviar clínico sensible a features públicas
11. no aceptar prompts que pidan diagnóstico o receta automática
12. feedback solo del dueño de la interacción
13. si proveedor falla, registrar interacción failed_provider y responder fallback controlado

REGLAS DE COSTO Y CUOTAS
1. Debe existir contador por usuario o rol
2. Debe existir costo estimado por interacción
3. Si supera el límite, bloquear
4. Exponer resumen de uso por feature y por período
5. Permitir cuotas distintas para patient, professional, laboratory y admin roles

AUDITORÍA OBLIGATORIA
Registrar audit_event en:
- cambio de feature policy
- cambio de quota
- cambio de provider/model activo
- uso administrativo sensible de IA
- bloqueos importantes de guardrail
Registrar ai_interactions en toda invocación permitida o rechazada.
Registrar ai_guardrail_events en denegaciones y redacciones.

PANTALLAS FLUTTER MÍNIMAS

PATIENT / PÚBLICO
1. caja de búsqueda inteligente
2. sugerencias de filtros
3. resumen asistido de professional/laboratory
4. historial propio de interacciones
5. feedback simple

PROFESSIONAL
1. asistente para bio pública
2. asistente para texto operativo al paciente
3. historial propio de interacciones
4. copiar/usar borrador manualmente

LABORATORY
1. asistente para descripción pública
2. asistente para texto de preparación no clínica
3. historial propio de interacciones

ADMIN MODERATION
1. clasificador asistido de reportes
2. resumen asistido de reportes

ADMIN PRIVACY / AUDITOR
1. resumen asistido de access logs
2. vista de interacciones administrativas
3. vista de eventos de guardrail

ADMIN IA
1. políticas por feature
2. cuotas
3. uso acumulado
4. errores/proveedor

SEEDS
- ai_providers:
  - mock
  - openrouter
- ai_feature_policies:
  - search_assistant
  - profile_summary
  - writing_assistant
  - moderation_classifier
  - audit_summarizer
- ai_models ejemplo:
  - mock/default
  - openrouter/model configurable por ENV

ORDEN EXACTO DE IMPLEMENTACIÓN
1. migraciones
2. seeds
3. modelos ORM
4. schemas
5. provider adapters
6. ai policy service
7. ai quota/cost service
8. ai interaction logger
9. ai guardrail service
10. search assistant service
11. profile summary service
12. writing assistant service
13. moderation classifier service
14. audit summarizer service
15. endpoints
16. tests backend
17. pantallas Flutter
18. integración Flutter-API
19. README paso 9

PRUEBAS AUTOMÁTICAS
1. búsqueda inteligente devuelve filtros estructurados válidos
2. profile_summary no usa datos privados
3. writing_assistant devuelve borrador y no persiste
4. moderation_classifier sugiere categoría sin resolver caso
5. audit_summarizer resume logs permitidos
6. rol no permitido es bloqueado
7. cuota excedida es bloqueada
8. intento de prompt clínico no permitido genera guardrail
9. proveedor fallido deja interacción registrada
10. feedback se guarda
11. costos y contadores se acumulan
12. admin no obtiene acceso clínico nuevo por IA
13. auditoría de cambios en policies y quotas funciona

CRITERIOS DE ACEPTACIÓN
- IA solo opera en casos no clínicos permitidos
- búsqueda inteligente ayuda sin inventar resultados
- resúmenes de perfil usan solo datos públicos
- redacción asistida requiere confirmación humana
- moderación asistida no sanciona automáticamente
- resumen de auditoría no rompe privacidad
- guardrails bloquean usos prohibidos
- costos y cuotas se controlan
- todo uso queda trazado
- tests pasan

SALIDA ESPERADA
Entregar directamente:
- migraciones
- modelos
- adapters
- servicios
- endpoints
- tests
- pantallas Flutter mínimas
- README breve

NO EXPLICAR DEMASIADO.
IMPLEMENTAR.
```

También se deja la versión corta, para gastar menos tokens en OpenCode:

```text
Implementar paso 9:
IA segura y útil para búsqueda, resúmenes y redacción no clínica.

Base existente:
FastAPI + PostgreSQL + Flutter.
Pasos 1 a 8 ya existen.

No implementar:
diagnóstico automático, receta automática, interpretación clínica, chatbot clínico autónomo, sanción automática.

Crear tablas:
ai_feature_policies
ai_providers
ai_models
ai_prompts_catalog
ai_interactions
ai_interaction_sources
ai_usage_quotas
ai_usage_counters
ai_feedback
ai_guardrail_events

Feature flags:
ai_assistant_enabled
ai_search_enabled
ai_writing_enabled
ai_moderation_assist_enabled
ai_audit_summary_enabled

Implementar adapters:
- MockAIProviderAdapter
- OpenRouterProviderAdapter

Implementar services:
- ai policy
- ai quota/cost
- ai interaction logger
- ai guardrail
- search assistant
- profile summary
- writing assistant
- moderation classifier
- audit summarizer

Casos permitidos:
- convertir texto libre a filtros de búsqueda
- resumir perfiles públicos
- ayudar a redactar bio pública y textos operativos
- clasificar reportes para moderación
- resumir access logs para privacidad/auditoría

Reglas:
- IA no toma decisiones clínicas
- IA no persiste automáticamente campos críticos
- IA usa solo contexto permitido
- IA no da acceso clínico nuevo
- guardrails para prompts sensibles, rol, cuota y costo
- toda interacción auditada
- prompt/response redactados

Endpoints:
POST /api/v1/ai/search-assistant
POST /api/v1/ai/profile-summary/professional/{slug}
POST /api/v1/ai/profile-summary/laboratory/{slug}
GET /api/v1/ai/interactions/me
POST /api/v1/ai/interactions/{id}/feedback

POST /api/v1/professionals/me/ai/writing-assistant/profile-bio
POST /api/v1/professionals/me/ai/writing-assistant/patient-message
GET /api/v1/professionals/me/ai/interactions

POST /api/v1/laboratories/me/ai/writing-assistant/profile-description
POST /api/v1/laboratories/me/ai/writing-assistant/preparation-text
GET /api/v1/laboratories/me/ai/interactions

POST /api/v1/admin/moderation/ai/classify-report/{report_id}
POST /api/v1/admin/moderation/ai/summarize-report/{report_id}

POST /api/v1/admin/privacy/ai/summarize-access-logs
POST /api/v1/privacy-auditor/ai/summarize-access-logs

GET /api/v1/admin/ai/providers
GET /api/v1/admin/ai/models
GET /api/v1/admin/ai/feature-policies
PUT /api/v1/admin/ai/feature-policies/{feature_code}
GET /api/v1/admin/ai/interactions
GET /api/v1/admin/ai/guardrail-events
GET /api/v1/admin/ai/usage
GET /api/v1/admin/ai/quotas
PUT /api/v1/admin/ai/quotas/{feature_code}

Tests:
- search assistant devuelve filtros válidos
- profile summary usa solo público
- writing assistant no persiste
- moderation classifier no resuelve solo
- audit summarizer no rompe privacidad
- rol bloqueado
- cuota bloqueada
- prompt clínico prohibido bloqueado
- provider failure registrado
- feedback guardado
- IA no da acceso clínico nuevo

Entregar código, migraciones, adapters, tests, Flutter mínimo y README.
```
