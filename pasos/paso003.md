Se deja el **paso 3** listo, masticado y comprimido para que OpenCode implemente **pagos + comisión + confirmación económica de la cita** sin gastar muchos tokens.

```text id="30841"
IMPLEMENTAR PASO 3 DEL MARKETPLACE DE SALUD.

CONTEXTO FIJO
- Stack: Flutter + FastAPI + PostgreSQL + Docker Compose.
- Paso 1 ya existe: auth, roles, verification, audit.
- Paso 2 ya existe: perfiles públicos, disponibilidades, slots, citas.
- No cambiar arquitectura.
- Mantener soft delete, auditoría, versionado, estados y reversibilidad.
- Admin no ve datos clínicos.

OBJETIVO
Implementar:
1. precios por profesional
2. checkout simple
3. intento de pago
4. pago registrado
5. comisión de plataforma
6. confirmación económica de la cita
7. cancelación con regla económica básica
8. liquidación pendiente al profesional
9. pantallas Flutter mínimas

NO IMPLEMENTAR
- pasarela real compleja si no es necesaria
- facturación electrónica
- split real bancario
- reembolsos automáticos externos
- suscripciones
- planes premium
- clínica
- recetas
- videollamada
- laboratorios
- reputación

ENFOQUE
Primero implementar pasarela abstracta + modo sandbox/manual.
Debe quedar preparado para integrar después proveedor real.

REGLAS DE NEGOCIO
1. Una cita reservada no queda económicamente confirmada hasta registrar pago exitoso.
2. La cita puede existir en estado operativo y estado financiero separados.
3. La plataforma cobra una comisión por cita.
4. La comisión debe quedar congelada al momento del pago.
5. Nunca borrar pagos ni transacciones.
6. Toda reversa debe ser por compensación o cambio de estado.
7. Toda acción económica crítica debe quedar auditada.
8. Si falla el pago, la cita no queda confirmada económicamente.
9. El paciente solo paga por sus propias citas.
10. El profesional no toca pagos del paciente.
11. Admin gestiona incidencias financieras, no datos clínicos.
12. Debe existir idempotencia para crear intentos de pago.
13. Valores monetarios siempre en decimal exacto.
14. Moneda inicial USD.
15. Timezone inicial America/Guayaquil.

MODELO
Separar:
- estado operativo de la cita
- estado financiero de la cita

TABLAS NUEVAS

1) pricing_policies
- id uuid pk
- code varchar unique not null
- name varchar not null
- commission_type varchar not null   # percentage, fixed
- commission_value numeric(10,2) not null
- is_active boolean default true
- created_at
- updated_at
- deleted_at null
- version int default 1

2) professional_prices
- id uuid pk
- professional_id fk not null
- modality_code varchar not null
- amount numeric(10,2) not null
- currency_code varchar(3) not null default 'USD'
- pricing_policy_id fk not null
- is_active boolean default true
- created_at
- updated_at
- deleted_at null
- version int default 1
- unique(professional_id, modality_code)

3) payment_intents
- id uuid pk
- appointment_id fk not null
- patient_id fk not null
- amount_total numeric(10,2) not null
- currency_code varchar(3) not null default 'USD'
- status varchar not null   # created, pending, authorized, paid, failed, expired, cancelled
- provider_code varchar not null   # sandbox
- provider_reference varchar null
- idempotency_key varchar unique not null
- expires_at timestamptz null
- created_at
- updated_at
- deleted_at null
- version int default 1

4) payments
- id uuid pk
- payment_intent_id fk not null unique
- appointment_id fk not null
- patient_id fk not null
- amount_total numeric(10,2) not null
- currency_code varchar(3) not null
- status varchar not null   # paid, partially_refunded, refunded, chargeback, voided
- paid_at timestamptz null
- external_reference varchar null
- reconciliation_status varchar not null default 'pending'
- created_at
- updated_at
- deleted_at null
- version int default 1

5) payment_transactions
- id uuid pk
- payment_id fk null
- payment_intent_id fk null
- transaction_type varchar not null   # intent_created, payment_succeeded, payment_failed, refund_requested, refund_applied, void_applied
- amount numeric(10,2) not null
- currency_code varchar(3) not null
- provider_code varchar not null
- provider_reference varchar null
- raw_response_json jsonb null
- status varchar not null
- created_at
- created_by null

6) appointment_financials
- id uuid pk
- appointment_id fk unique not null
- professional_price_id fk not null
- gross_amount numeric(10,2) not null
- platform_commission_type varchar not null
- platform_commission_value numeric(10,2) not null
- platform_commission_amount numeric(10,2) not null
- professional_net_amount numeric(10,2) not null
- currency_code varchar(3) not null default 'USD'
- payment_status varchar not null   # unpaid, pending, paid, refunded, partially_refunded, failed
- settlement_status varchar not null   # not_ready, pending_settlement, settled, cancelled
- created_at
- updated_at
- deleted_at null
- version int default 1

7) refunds
- id uuid pk
- payment_id fk not null
- appointment_id fk not null
- amount numeric(10,2) not null
- currency_code varchar(3) not null
- reason varchar not null
- status varchar not null   # requested, approved, rejected, applied
- requested_by_user_id fk null
- approved_by_user_id fk null
- created_at
- updated_at
- deleted_at null
- version int default 1

8) settlement_batches
- id uuid pk
- batch_code varchar unique not null
- professional_id fk not null
- total_gross numeric(10,2) not null
- total_commission numeric(10,2) not null
- total_net numeric(10,2) not null
- currency_code varchar(3) not null default 'USD'
- status varchar not null   # draft, generated, paid, cancelled
- generated_at timestamptz null
- paid_at timestamptz null
- created_at
- updated_at
- deleted_at null
- version int default 1

9) settlement_batch_items
- id uuid pk
- settlement_batch_id fk not null
- appointment_id fk not null
- appointment_financial_id fk not null
- gross_amount numeric(10,2) not null
- commission_amount numeric(10,2) not null
- net_amount numeric(10,2) not null
- created_at

CAMBIOS A TABLA appointments
Agregar:
- financial_status varchar not null default 'unpaid'
Valores:
- unpaid
- payment_pending
- paid
- refunded
- failed
- cancelled

ESTADOS PAYMENT_INTENT
- created
- pending
- authorized
- paid
- failed
- expired
- cancelled

ESTADOS PAYMENTS
- paid
- partially_refunded
- refunded
- chargeback
- voided

TRANSICIONES FINANCIERAS DE CITA
- unpaid -> payment_pending
- payment_pending -> paid
- payment_pending -> failed
- paid -> refunded
- paid -> partially_refunded
- failed -> cancelled
No permitir otras.

REGLA DE COMISIÓN
- leer de pricing_policy asociada al professional_price
- congelar porcentaje/valor y monto calculado en appointment_financials al crear el intent o al pagar
- no recalcular histórico si luego cambia la política

REGLA DE CANCELACIÓN BÁSICA
1. Si la cita está unpaid o payment_pending, cancelar sin refund.
2. Si la cita está paid y aún no está completed:
   - permitir refund manual total en esta fase
3. Si la cita está completed:
   - no refund automático
   - solo flujo administrativo posterior
No inventar reglas más complejas.

PASARELA
Crear interfaz:
- PaymentProvider.create_intent()
- PaymentProvider.confirm_payment()
- PaymentProvider.fail_payment()
- PaymentProvider.refund_payment()

Implementar SandboxPaymentProvider:
- éxito manual
- fallo manual
- sin integración externa real

ENDPOINTS NUEVOS

PUBLIC/PATIENT
- GET /api/v1/patient/appointments/{id}/checkout
- POST /api/v1/patient/appointments/{id}/payment-intent
- POST /api/v1/patient/payment-intents/{id}/confirm-sandbox
- POST /api/v1/patient/payment-intents/{id}/fail-sandbox
- GET /api/v1/patient/payments
- GET /api/v1/patient/payments/{id}
- POST /api/v1/patient/appointments/{id}/cancel-with-refund-request

PROFESSIONAL
- GET /api/v1/professionals/me/prices
- PUT /api/v1/professionals/me/prices
- GET /api/v1/professionals/me/earnings/pending
- GET /api/v1/professionals/me/earnings/settlements

ADMIN
- GET /api/v1/admin/payments
- GET /api/v1/admin/payments/{id}
- GET /api/v1/admin/refunds
- POST /api/v1/admin/refunds/{id}/approve
- POST /api/v1/admin/refunds/{id}/reject
- POST /api/v1/admin/refunds/{id}/apply-sandbox
- GET /api/v1/admin/settlements/pending
- POST /api/v1/admin/settlements/generate/{professional_id}
- POST /api/v1/admin/settlements/{batch_id}/mark-paid
- GET /api/v1/admin/audit-events?entity_type=payment

REQUESTS CLAVE

PUT /professionals/me/prices
input:
- modality_code
- amount
output:
- professional_price_id
- amount
- currency_code
- pricing_policy

POST /patient/appointments/{id}/payment-intent
input:
- idempotency_key
output:
- payment_intent_id
- amount_total
- status
- expires_at

POST /patient/payment-intents/{id}/confirm-sandbox
output:
- payment_id
- payment_status
- appointment_financial_status
- appointment_operational_status

GET /patient/appointments/{id}/checkout
output:
- appointment_id
- professional_name
- modality_code
- gross_amount
- currency_code
- commission_amount optional hidden if desired
- amount_total
- payment_status

SERVICIOS
1. pricing service
2. payment intent service
3. sandbox payment provider
4. payment confirmation service
5. refund service
6. settlement service
7. audit service hook

FLUJO DE PAGO
1. paciente crea payment_intent para una cita propia
2. sistema valida cita y precio activo
3. sistema crea appointment_financials si no existe
4. sistema crea payment_intent con idempotency_key única
5. paciente confirma sandbox
6. sistema crea payment
7. sistema crea payment_transaction
8. sistema actualiza appointment.financial_status = paid
9. sistema actualiza appointment_financials.payment_status = paid
10. sistema deja settlement_status = pending_settlement
11. sistema registra audit_event

REGLAS DE SEGURIDAD
- paciente solo opera pagos de sus citas
- professional no puede confirmar pagos
- admin no altera monto pagado manualmente sin auditoría
- refund requiere motivo
- apply refund cambia estados, no borra nada
- endpoints financieros requieren auth
- admin ve datos económicos y operativos, no clínicos

CONCURRENCIA
Al confirmar pago:
1. transacción
2. lock sobre payment_intent
3. verificar que no esté ya paid
4. crear payment una sola vez
5. actualizar appointment y appointment_financials
6. insertar transaction
7. commit

Al crear intent:
- usar idempotency_key única
- si misma key ya existe para misma cita y sigue válida, retornar la existente

PRUEBAS AUTOMÁTICAS
1. professional puede definir precio por modalidad
2. paciente obtiene checkout correcto
3. crear payment_intent funciona
4. misma idempotency_key no duplica intent
5. confirm sandbox crea payment una sola vez
6. cita cambia a paid
7. appointment_financials calcula comisión y neto correctamente
8. fail sandbox deja cita failed o payment_pending según flujo elegido
9. cancel unpaid no genera refund
10. cancel paid crea refund request
11. approve refund funciona
12. apply sandbox refund cambia estados correctamente
13. settlement pending lista citas pagadas no liquidadas
14. generar settlement batch funciona
15. mark-paid de settlement batch funciona
16. audit_event se registra en intent, pago, refund, settlement
17. patient no ve pagos ajenos
18. professional no accede a pagos del paciente

PANTALLAS FLUTTER MÍNIMAS

PACIENTE
1. checkout de cita
2. crear intent
3. botón pagar sandbox éxito
4. botón simular fallo
5. listado de pagos
6. solicitar cancelación con refund

PROFESSIONAL
1. configurar precios por modalidad
2. ver ganancias pendientes
3. ver lotes liquidados

ADMIN
1. listado de pagos
2. detalle de pago
3. listado de refunds
4. aprobar/rechazar/aplicar refund sandbox
5. generar settlement batch
6. marcar settlement como pagado

SEEDS
- pricing_policy default_percentage_15
  commission_type=percentage
  commission_value=15.00
- feature_flag payments_enabled=true
- feature_flag refunds_enabled=true
- feature_flag settlements_enabled=true

ORDEN EXACTO DE IMPLEMENTACIÓN
1. migraciones
2. seeds
3. modelos ORM
4. schemas
5. pricing service
6. payment provider sandbox
7. payment intent service
8. payment confirmation service
9. refund service
10. settlement service
11. endpoints
12. tests backend
13. pantallas Flutter
14. integración Flutter-API
15. README paso 3

CRITERIOS DE ACEPTACIÓN
- professional configura precios
- paciente ve checkout
- paciente genera payment_intent
- confirmación sandbox registra pago
- comisión y neto quedan congelados
- cita queda paid en financiero
- refund request funciona
- admin puede aplicar refund sandbox
- settlement batch puede generarse
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

También se deja una **versión aún más corta** para gastar menos tokens:

```text id="14392"
Implementar paso 3:
pagos + comisión + confirmación económica de cita.

Base existente:
FastAPI + PostgreSQL + Flutter.
Paso 1 y 2 ya existen.

No implementar:
pasarela real compleja, facturación electrónica, suscripciones, clínica, videollamada, laboratorios.

Crear tablas:
pricing_policies
professional_prices
payment_intents
payments
payment_transactions
appointment_financials
refunds
settlement_batches
settlement_batch_items

Agregar a appointments:
financial_status = unpaid|payment_pending|paid|refunded|failed|cancelled

Reglas:
- cita no queda confirmada económicamente hasta pago exitoso
- comisión se congela al pagar
- nunca borrar pagos
- refund por compensación/estado
- auditoría obligatoria
- paciente solo paga sus citas
- idempotency_key obligatoria
- USD

Implementar sandbox payment provider:
create_intent
confirm_payment
fail_payment
refund_payment

Endpoints:
GET /patient/appointments/{id}/checkout
POST /patient/appointments/{id}/payment-intent
POST /patient/payment-intents/{id}/confirm-sandbox
POST /patient/payment-intents/{id}/fail-sandbox
GET /patient/payments
GET /patient/payments/{id}
POST /patient/appointments/{id}/cancel-with-refund-request

GET /professionals/me/prices
PUT /professionals/me/prices
GET /professionals/me/earnings/pending
GET /professionals/me/earnings/settlements

GET /admin/payments
GET /admin/payments/{id}
GET /admin/refunds
POST /admin/refunds/{id}/approve
POST /admin/refunds/{id}/reject
POST /admin/refunds/{id}/apply-sandbox
GET /admin/settlements/pending
POST /admin/settlements/generate/{professional_id}
POST /admin/settlements/{batch_id}/mark-paid

Pruebas:
- precio por modalidad
- checkout correcto
- idempotencia
- confirm sandbox crea un solo payment
- comisión correcta
- refund request
- refund apply
- settlement batch
- auditoría
- aislamiento por permisos

Entregar código, migraciones, tests, Flutter mínimo y README.
```

Conviene que el siguiente sea el **paso 4 masticado**: **teleconsulta básica + enlace externo + recetas e indicaciones simples sin historia clínica completa**.
