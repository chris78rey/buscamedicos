<script setup lang="ts">
import { FetchError } from 'ofetch'

import type { PaymentResponse } from '~/types/appointment'

definePageMeta({
  layout: 'patient',
  middleware: ['auth', 'role'],
  roles: ['patient'],
})

const { getMyPayments } = useApi()

const payments = ref<PaymentResponse[]>([])
const loading = ref(false)
const errorMessage = ref('')

const statusMeta: Record<string, { label: string; color: string }> = {
  paid: { label: 'Pagado', color: 'success' },
  partially_refunded: { label: 'Parcialmente reembolsado', color: 'warning' },
  refunded: { label: 'Reembolsado', color: 'info' },
  chargeback: { label: 'Contracargo', color: 'error' },
  voided: { label: 'Anulado', color: 'grey' },
}

function resolveStatus(status: string) {
  return statusMeta[status] ?? { label: status, color: 'grey' }
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

async function loadPayments() {
  loading.value = true
  errorMessage.value = ''

  try {
    payments.value = await getMyPayments()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudieron cargar los pagos.'
    }
    else {
      errorMessage.value = 'Error inesperado al cargar los pagos.'
    }
    payments.value = []
  }
  finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPayments()
})
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <div class="d-flex justify-space-between align-center flex-wrap ga-3">
      <div>
        <h2 class="text-h5">Mis pagos</h2>
        <p class="text-body-2 text-medium-emphasis mb-0">
          Historial de pagos realizados.
        </p>
      </div>

      <div class="d-flex flex-wrap ga-3">
        <v-btn
          color="primary"
          prepend-icon="mdi-calendar-check"
          variant="tonal"
          @click="$router.push('/patient/appointments')"
        >
          Ver citas
        </v-btn>

        <v-btn
          :loading="loading"
          prepend-icon="mdi-refresh"
          variant="outlined"
          @click="loadPayments"
        >
          Recargar
        </v-btn>
      </div>
    </div>

    <v-alert
      v-if="errorMessage"
      type="error"
      variant="tonal"
    >
      {{ errorMessage }}
    </v-alert>

    <v-skeleton-loader
      v-else-if="loading"
      rounded="xl"
      type="card, card, card"
    />

    <v-alert
      v-else-if="!payments.length"
      type="info"
      variant="tonal"
    >
      No tiene pagos registrados.
    </v-alert>

    <v-row v-else>
      <v-col
        v-for="payment in payments"
        :key="payment.id"
        cols="12"
        md="6"
      >
        <v-card class="h-100" rounded="xl">
          <v-card-item>
            <template #append>
              <v-chip
                :color="resolveStatus(payment.status).color"
                variant="tonal"
              >
                {{ resolveStatus(payment.status).label }}
              </v-chip>
            </template>

            <v-card-title>
              {{ formatCurrency(payment.amount_total, payment.currency_code) }}
            </v-card-title>

            <v-card-subtitle>
              Pagado: {{ formatDateTime(payment.paid_at) }}
            </v-card-subtitle>
          </v-card-item>

          <v-card-text class="d-flex flex-column ga-3">
            <div>
              <div class="text-caption text-medium-emphasis">ID Pago</div>
              <div class="text-body-2 text-truncate" style="max-width: 250px;">
                {{ payment.id }}
              </div>
            </div>

            <div v-if="payment.external_reference">
              <div class="text-caption text-medium-emphasis">Referencia externa</div>
              <div class="text-body-2 text-truncate" style="max-width: 250px;">
                {{ payment.external_reference }}
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
