<script setup lang="ts">
import { FetchError } from 'ofetch'

import type { CheckoutResponse, PaymentIntentResponse, PaymentIntentConfirmResponse } from '~/types/appointment'

definePageMeta({
  layout: 'patient',
  middleware: ['auth', 'role'],
  roles: ['patient'],
})

const route = useRoute()
const router = useRouter()
const {
  getCheckout,
  createPaymentIntent,
  confirmSandboxPayment,
  failSandboxPayment,
} = useApi()

const appointmentId = computed(() => String(route.params.id ?? ''))

const checkout = ref<CheckoutResponse | null>(null)
const paymentIntent = ref<PaymentIntentResponse | null>(null)
const confirmResult = ref<PaymentIntentConfirmResponse | null>(null)

const loadingCheckout = ref(false)
const loadingIntent = ref(false)
const loadingConfirm = ref(false)
const loadingFail = ref(false)

const checkoutError = ref('')
const intentError = ref('')
const confirmError = ref('')

const idempotencyKey = ref('')

const financialStatusMeta: Record<string, { label: string; color: string }> = {
  unpaid: { label: 'Sin pagar', color: 'grey' },
  payment_pending: { label: 'Pendiente de pago', color: 'warning' },
  paid: { label: 'Pagado', color: 'success' },
  refunded: { label: 'Reembolsado', color: 'info' },
  failed: { label: 'Fallido', color: 'error' },
}

const paymentIntentStatusMeta: Record<string, { label: string; color: string }> = {
  created: { label: 'Creado', color: 'grey' },
  pending: { label: 'Pendiente', color: 'warning' },
  authorized: { label: 'Autorizado', color: 'primary' },
  paid: { label: 'Pagado', color: 'success' },
  failed: { label: 'Fallido', color: 'error' },
  expired: { label: 'Expirado', color: 'deep-orange' },
  cancelled: { label: 'Cancelado', color: 'error' },
}

function resolveFinancialStatus(status: string | undefined) {
  if (!status) return { label: 'Desconocido', color: 'grey' }
  return financialStatusMeta[status] ?? { label: status, color: 'grey' }
}

function resolveIntentStatus(status: string | undefined) {
  if (!status) return { label: 'Desconocido', color: 'grey' }
  return paymentIntentStatusMeta[status] ?? { label: status, color: 'grey' }
}

function formatCurrency(value?: number | null, currency = 'USD') {
  if (value === null || value === undefined) return 'N/A'
  return new Intl.NumberFormat('es-EC', {
    style: 'currency',
    currency,
  }).format(value)
}

function formatDateTime(value?: string | null) {
  if (!value) return 'N/A'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleString('es-EC', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function generateIdempotencyKey() {
  return `${appointmentId.value}-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`
}

async function loadCheckout() {
  loadingCheckout.value = true
  checkoutError.value = ''

  try {
    checkout.value = await getCheckout(appointmentId.value)
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      checkoutError.value = error.data?.detail?.toString() || 'No se pudo cargar el checkout.'
    }
    else {
      checkoutError.value = 'Error al cargar el checkout.'
    }
    checkout.value = null
  }
  finally {
    loadingCheckout.value = false
  }
}

async function handleCreateIntent() {
  if (!checkout.value) return

  loadingIntent.value = true
  intentError.value = ''

  try {
    idempotencyKey.value = generateIdempotencyKey()
    paymentIntent.value = await createPaymentIntent(appointmentId.value, idempotencyKey.value)
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      intentError.value = error.data?.detail?.toString() || 'No se pudo crear el intento de pago.'
    }
    else {
      intentError.value = 'Error al crear el intento de pago.'
    }
    paymentIntent.value = null
  }
  finally {
    loadingIntent.value = false
  }
}

async function handleConfirmPayment() {
  if (!paymentIntent.value) return

  loadingConfirm.value = true
  confirmError.value = ''

  try {
    confirmResult.value = await confirmSandboxPayment(paymentIntent.value.id)
    await loadCheckout()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      confirmError.value = error.data?.detail?.toString() || 'No se pudo confirmar el pago.'
    }
    else {
      confirmError.value = 'Error al confirmar el pago.'
    }
  }
  finally {
    loadingConfirm.value = false
  }
}

async function handleFailPayment() {
  if (!paymentIntent.value) return

  loadingFail.value = true

  try {
    await failSandboxPayment(paymentIntent.value.id)
    paymentIntent.value = null
    await loadCheckout()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      intentError.value = error.data?.detail?.toString() || 'Error al simular fallo.'
    }
  }
  finally {
    loadingFail.value = false
  }
}

onMounted(async () => {
  await loadCheckout()
})
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <div class="d-flex flex-wrap ga-3">
      <v-btn
        prepend-icon="mdi-arrow-left"
        variant="text"
        @click="router.push('/patient/appointments')"
      >
        Volver a citas
      </v-btn>
    </div>

    <v-alert
      v-if="checkoutError"
      type="error"
      variant="tonal"
    >
      {{ checkoutError }}
    </v-alert>

    <v-skeleton-loader
      v-else-if="loadingCheckout"
      rounded="xl"
      type="card, card"
    />

    <template v-else-if="checkout">
      <v-card rounded="xl">
        <v-card-item>
          <v-card-title>Checkout de cita</v-card-title>
          <v-card-subtitle>
            Cita: {{ checkout.appointment_id.slice(0, 8) }}...
          </v-card-subtitle>
        </v-card-item>

        <v-card-text class="d-flex flex-column ga-4">
          <div class="d-flex flex-wrap justify-space-between">
            <div>
              <div class="text-caption text-medium-emphasis">Profesional</div>
              <div class="text-body-1">{{ checkout.professional_name }}</div>
            </div>
            <div>
              <div class="text-caption text-medium-emphasis">Modalidad</div>
              <div class="text-body-1">{{ checkout.modality_code }}</div>
            </div>
            <div>
              <div class="text-caption text-medium-emphasis">Estado financiero</div>
              <v-chip
                :color="resolveFinancialStatus(checkout.payment_status).color"
                size="small"
                variant="tonal"
              >
                {{ resolveFinancialStatus(checkout.payment_status).label }}
              </v-chip>
            </div>
          </div>

          <v-divider />

          <div class="d-flex flex-wrap justify-space-between align-center">
            <div>
              <div class="text-caption text-medium-emphasis">Monto bruto</div>
              <div class="text-body-2">{{ formatCurrency(checkout.gross_amount, checkout.currency_code) }}</div>
            </div>
            <div class="text-h5 font-weight-bold">
              Total: {{ formatCurrency(checkout.amount_total, checkout.currency_code) }}
            </div>
          </div>
        </v-card-text>
      </v-card>

      <v-card v-if="checkout.payment_status === 'paid'" rounded="xl">
        <v-card-item>
          <template #prepend>
            <v-icon color="success" icon="mdi-check-circle" />
          </template>
          <v-card-title>Pago confirmado</v-card-title>
          <v-card-subtitle>Su cita ha sido pagada exitosamente.</v-card-subtitle>
        </v-card-item>
        <v-card-actions>
          <v-btn
            color="primary"
            variant="tonal"
            @click="router.push('/patient/appointments')"
          >
            Ver mis citas
          </v-btn>
        </v-card-actions>
      </v-card>

      <v-card v-else-if="checkout.payment_status === 'unpaid'" rounded="xl">
        <v-card-item>
          <v-card-title>Pago pendiente</v-card-title>
          <v-card-subtitle>
            Debe generar un intention de pago para continuar.
          </v-card-subtitle>
        </v-card-item>

        <v-card-text>
          <v-alert
            v-if="intentError"
            class="mb-4"
            type="error"
            variant="tonal"
          >
            {{ intentError }}
          </v-alert>

          <v-alert
            v-if="confirmResult"
            class="mb-4"
            type="success"
            variant="tonal"
          >
            Pago confirmado. Payment ID: {{ confirmResult.payment_id }}
          </v-alert>

          <v-btn
            v-if="!paymentIntent"
            :loading="loadingIntent"
            color="primary"
            prepend-icon="mdi-credit-card-outline"
            size="large"
            @click="handleCreateIntent"
          >
            Generar intencion de pago
          </v-btn>

          <template v-else>
            <v-divider class="my-4" />

            <div class="d-flex flex-wrap justify-space-between mb-4">
              <div>
                <div class="text-caption text-medium-emphasis">ID intencion</div>
                <div class="text-body-2 text-truncate" style="max-width: 300px;">
                  {{ paymentIntent.id }}
                </div>
              </div>
              <div>
                <div class="text-caption text-medium-emphasis">Monto</div>
                <div class="text-body-2">
                  {{ formatCurrency(paymentIntent.amount_total) }}
                </div>
              </div>
              <div>
                <div class="text-caption text-medium-emphasis">Estado</div>
                <v-chip
                  :color="resolveIntentStatus(paymentIntent.status).color"
                  size="small"
                  variant="tonal"
                >
                  {{ resolveIntentStatus(paymentIntent.status).label }}
                </v-chip>
              </div>
              <div v-if="paymentIntent.expires_at">
                <div class="text-caption text-medium-emphasis">Expira</div>
                <div class="text-body-2">{{ formatDateTime(paymentIntent.expires_at) }}</div>
              </div>
            </div>

            <v-alert
              v-if="confirmError"
              class="mb-4"
              type="error"
              variant="tonal"
            >
              {{ confirmError }}
            </v-alert>

            <div class="d-flex flex-wrap ga-3">
              <v-btn
                :loading="loadingConfirm"
                color="success"
                prepend-icon="mdi-check"
                @click="handleConfirmPayment"
              >
                Confirmar pago (sandbox)
              </v-btn>

              <v-btn
                :loading="loadingFail"
                color="error"
                prepend-icon="mdi-close"
                variant="outlined"
                @click="handleFailPayment"
              >
                Simular fallo
              </v-btn>

              <v-btn
                variant="text"
                @click="paymentIntent = null"
              >
                Cancelar
              </v-btn>
            </div>
          </template>
        </v-card-text>
      </v-card>
    </template>
  </div>
</template>
