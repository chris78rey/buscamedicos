<script setup lang="ts">
import { FetchError } from 'ofetch'

definePageMeta({
  layout: 'professional',
  middleware: ['auth', 'role'],
  roles: ['professional'],
})

const { getPendingEarnings, getMySettlements } = useApi()

type PendingEarnings = {
  total_pending_gross: number
  total_pending_commission: number
  total_pending_net: number
  currency_code: string
  appointments_count: number
}

type SettlementBatch = {
  id: string
  batch_code: string
  total_gross: number
  total_commission: number
  total_net: number
  currency_code: string
  status: string
  generated_at?: string | null
  paid_at?: string | null
}

const pending = ref<PendingEarnings | null>(null)
const settlements = ref<SettlementBatch[]>([])

const loadingPending = ref(false)
const loadingSettlements = ref(false)
const errorPending = ref('')
const errorSettlements = ref('')

const settlementStatusMeta: Record<string, { label: string; color: string }> = {
  draft: { label: 'Borrador', color: 'grey' },
  generated: { label: 'Generado', color: 'primary' },
  paid: { label: 'Pagado', color: 'success' },
  cancelled: { label: 'Cancelado', color: 'error' },
}

function resolveSettlementStatus(status: string) {
  return settlementStatusMeta[status] ?? { label: status, color: 'grey' }
}

function formatCurrency(value?: number | null, currency = 'USD') {
  if (value === null || value === undefined) return '$0.00'
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

async function loadPendingEarnings() {
  loadingPending.value = true
  errorPending.value = ''

  try {
    pending.value = await getPendingEarnings()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorPending.value = error.data?.detail?.toString() || 'No se pudieron cargar las ganancias pendientes.'
    }
    else {
      errorPending.value = 'Error al cargar ganancias pendientes.'
    }
    pending.value = null
  }
  finally {
    loadingPending.value = false
  }
}

async function loadSettlements() {
  loadingSettlements.value = true
  errorSettlements.value = ''

  try {
    settlements.value = await getMySettlements()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorSettlements.value = error.data?.detail?.toString() || 'No se pudieron cargar las liquidaciones.'
    }
    else {
      errorSettlements.value = 'Error al cargar liquidaciones.'
    }
    settlements.value = []
  }
  finally {
    loadingSettlements.value = false
  }
}

async function loadAll() {
  await Promise.all([loadPendingEarnings(), loadSettlements()])
}

onMounted(() => {
  loadAll()
})
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <div class="d-flex justify-space-between align-center flex-wrap ga-3">
      <div>
        <h2 class="text-h5">Ganancias y liquidaciones</h2>
        <p class="text-body-2 text-medium-emphasis mb-0">
          Resumen de ganancias pendientes y lotes de liquidacion.
        </p>
      </div>

      <v-btn
        :loading="loadingPending || loadingSettlements"
        prepend-icon="mdi-refresh"
        variant="outlined"
        @click="loadAll"
      >
        Recargar
      </v-btn>
    </div>

    <v-card rounded="xl">
      <v-card-item>
        <v-card-title>Ganancias pendientes</v-card-title>
        <v-card-subtitle>
          Citas pagadas awaiting liquidacion.
        </v-card-subtitle>
      </v-card-item>

      <v-card-text>
        <v-alert
          v-if="errorPending"
          type="error"
          variant="tonal"
          class="mb-4"
        >
          {{ errorPending }}
        </v-alert>

        <v-skeleton-loader
          v-else-if="loadingPending"
          rounded="xl"
          type="card"
        />

        <template v-else-if="pending">
          <v-row>
            <v-col cols="6" md="3">
              <v-card color="grey-lighten-4" rounded="lg">
                <v-card-text class="text-center">
                  <div class="text-caption text-medium-emphasis">Citas pendientes</div>
                  <div class="text-h4 font-weight-bold">{{ pending.appointments_count }}</div>
                </v-card-text>
              </v-card>
            </v-col>

            <v-col cols="6" md="3">
              <v-card color="grey-lighten-4" rounded="lg">
                <v-card-text class="text-center">
                  <div class="text-caption text-medium-emphasis">Monto bruto</div>
                  <div class="text-h6">{{ formatCurrency(pending.total_pending_gross, pending.currency_code) }}</div>
                </v-card-text>
              </v-card>
            </v-col>

            <v-col cols="6" md="3">
              <v-card color="grey-lighten-4" rounded="lg">
                <v-card-text class="text-center">
                  <div class="text-caption text-medium-emphasis">Comision plataforma</div>
                  <div class="text-h6 text-error">
                    -{{ formatCurrency(pending.total_pending_commission, pending.currency_code) }}
                  </div>
                </v-card-text>
              </v-card>
            </v-col>

            <v-col cols="6" md="3">
              <v-card color="success-lighten-5" rounded="lg">
                <v-card-text class="text-center">
                  <div class="text-caption text-medium-emphasis">Neto a recibir</div>
                  <div class="text-h5 font-weight-bold text-success">
                    {{ formatCurrency(pending.total_pending_net, pending.currency_code) }}
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </template>

        <v-alert
          v-else
          type="info"
          variant="tonal"
        >
          No hay ganancias pendientes de liquidacion.
        </v-alert>
      </v-card-text>
    </v-card>

    <v-card rounded="xl">
      <v-card-item>
        <v-card-title>Lotes de liquidacion</v-card-title>
        <v-card-subtitle>
          Historial de liquidaciones generadas y pagadas.
        </v-card-subtitle>
      </v-card-item>

      <v-card-text>
        <v-alert
          v-if="errorSettlements"
          type="error"
          variant="tonal"
          class="mb-4"
        >
          {{ errorSettlements }}
        </v-alert>

        <v-skeleton-loader
          v-else-if="loadingSettlements"
          rounded="xl"
          type="card, card"
        />

        <v-alert
          v-else-if="!settlements.length"
          type="info"
          variant="tonal"
        >
          No hay lotes de liquidacion registrados.
        </v-alert>

        <v-list v-else lines="two">
          <v-list-item
            v-for="batch in settlements"
            :key="batch.id"
          >
            <template #prepend>
              <v-icon
                :color="batch.status === 'paid' ? 'success' : 'primary'"
                :icon="batch.status === 'paid' ? 'mdi-check-circle' : 'mdi-file-document-outline'"
              />
            </template>

            <v-list-item-title>
              {{ batch.batch_code }}
            </v-list-item-title>

            <v-list-item-subtitle>
              <div class="d-flex flex-wrap ga-4">
                <span>Neto: <strong>{{ formatCurrency(batch.total_net, batch.currency_code) }}</strong></span>
                <span>Comision: {{ formatCurrency(batch.total_commission, batch.currency_code) }}</span>
              </div>
            </v-list-item-subtitle>

            <template #append>
              <div class="d-flex flex-column align-end ga-1">
                <v-chip
                  :color="resolveSettlementStatus(batch.status).color"
                  size="small"
                  variant="tonal"
                >
                  {{ resolveSettlementStatus(batch.status).label }}
                </v-chip>
                <span class="text-caption text-medium-emphasis">
                  {{ batch.status === 'paid' ? `Pagado: ${formatDateTime(batch.paid_at)}` : `Generado: ${formatDateTime(batch.generated_at)}` }}
                </span>
              </div>
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
  </div>
</template>
