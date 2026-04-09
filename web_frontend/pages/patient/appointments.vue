<script setup lang="ts">
import { FetchError } from 'ofetch'

import type { AppointmentSummary } from '~/types/appointment'

definePageMeta({
  layout: 'patient',
  middleware: ['auth', 'role'],
  roles: ['patient'],
})

const { getMyAppointments } = useApi()

const appointments = ref<AppointmentSummary[]>([])
const loading = ref(false)
const errorMessage = ref('')

const statusMeta: Record<string, { label: string; color: string }> = {
  pending_confirmation: {
    label: 'Pendiente de confirmacion',
    color: 'warning',
  },
  confirmed: {
    label: 'Confirmada',
    color: 'primary',
  },
  completed: {
    label: 'Completada',
    color: 'success',
  },
  cancelled_by_patient: {
    label: 'Cancelada por paciente',
    color: 'error',
  },
  cancelled_by_professional: {
    label: 'Cancelada por profesional',
    color: 'error',
  },
  no_show_patient: {
    label: 'Paciente no asistio',
    color: 'deep-orange',
  },
  no_show_professional: {
    label: 'Profesional no asistio',
    color: 'deep-orange',
  },
}

const financialStatusMeta: Record<string, { label: string; color: string }> = {
  unpaid: { label: 'Sin pagar', color: 'grey' },
  payment_pending: { label: 'Pago pendiente', color: 'warning' },
  paid: { label: 'Pagado', color: 'success' },
  refunded: { label: 'Reembolsado', color: 'info' },
  partially_refunded: { label: 'Parcialmente reembolsado', color: 'warning' },
  failed: { label: 'Fallido', color: 'error' },
}

function resolveStatus(status: string) {
  return statusMeta[status] ?? {
    label: status,
    color: 'grey',
  }
}

function resolveFinancialStatus(status: string | undefined) {
  if (!status) return { label: 'Sin info', color: 'grey' }
  return financialStatusMeta[status] ?? { label: status, color: 'grey' }
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return 'Sin fecha'
  }

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }

  return parsed.toLocaleString('es-EC', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function formatModality(value?: string | null) {
  if (!value) {
    return 'Modalidad no disponible'
  }

  const labels: Record<string, string> = {
    in_person_consultorio: 'Consulta presencial',
    teleconsulta: 'Teleconsulta',
  }

  return labels[value] ?? value
}

async function loadAppointments() {
  loading.value = true
  errorMessage.value = ''

  try {
    appointments.value = await getMyAppointments()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudieron consultar las citas.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado al cargar las citas.'
    }

    appointments.value = []
  }
  finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAppointments()
})
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <div class="d-flex justify-space-between align-center flex-wrap ga-3">
      <div>
        <h2 class="text-h5">Mis citas</h2>
        <p class="text-body-2 text-medium-emphasis mb-0">
          Se listan las citas del paciente en orden descendente por fecha.
        </p>
      </div>

      <div class="d-flex flex-wrap ga-3">
        <v-btn
          color="primary"
          prepend-icon="mdi-magnify"
          variant="tonal"
          @click="$router.push('/patient/professionals')"
        >
          Buscar profesionales
        </v-btn>

        <v-btn
          :loading="loading"
          prepend-icon="mdi-refresh"
          variant="outlined"
          @click="loadAppointments"
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
      type="article, article, article"
    />

    <v-alert
      v-else-if="!appointments.length"
      type="info"
      variant="tonal"
    >
      El paciente todavia no registra citas. Se puede ir a la busqueda de profesionales para crear la primera.
    </v-alert>

    <v-row v-else>
      <v-col
        v-for="appointment in appointments"
        :key="appointment.id"
        cols="12"
        md="6"
      >
        <v-card class="h-100" rounded="xl">
          <v-card-item>
            <template #append>
              <v-chip
                :color="resolveStatus(appointment.status).color"
                variant="tonal"
              >
                {{ resolveStatus(appointment.status).label }}
              </v-chip>
            </template>

            <v-card-title>
              {{ appointment.public_code || `Cita ${appointment.id.slice(0, 8)}` }}
            </v-card-title>

            <v-card-subtitle>
              {{ formatModality(appointment.modality_code) }}
            </v-card-subtitle>
          </v-card-item>

          <v-card-text class="d-flex flex-column ga-3">
            <div class="d-flex flex-wrap justify-space-between align-center">
              <div>
                <div class="text-caption text-medium-emphasis">Inicio</div>
                <div class="text-body-2">{{ formatDateTime(appointment.scheduled_start) }}</div>
              </div>
              <div>
                <div class="text-caption text-medium-emphasis">Fin</div>
                <div class="text-body-2">{{ formatDateTime(appointment.scheduled_end) }}</div>
              </div>
              <div>
                <div class="text-caption text-medium-emphasis">Estado pago</div>
                <v-chip
                  :color="resolveFinancialStatus(appointment.financial_status).color"
                  size="small"
                  variant="tonal"
                >
                  {{ resolveFinancialStatus(appointment.financial_status).label }}
                </v-chip>
              </div>
            </div>

            <div v-if="appointment.patient_note">
              <div class="text-caption text-medium-emphasis">Nota del paciente</div>
              <div class="text-body-2" style="white-space: pre-line;">
                {{ appointment.patient_note }}
              </div>
            </div>

            <div v-if="appointment.cancellation_reason">
              <div class="text-caption text-medium-emphasis">Motivo de cancelacion</div>
              <div class="text-body-2">{{ appointment.cancellation_reason }}</div>
            </div>

            <div v-if="appointment.reschedule_reason">
              <div class="text-caption text-medium-emphasis">Motivo de reagendamiento</div>
              <div class="text-body-2">{{ appointment.reschedule_reason }}</div>
            </div>
          </v-card-text>

          <v-card-actions v-if="appointment.financial_status === 'unpaid' || appointment.financial_status === 'payment_pending'">
            <v-spacer />
            <v-btn
              color="primary"
              prepend-icon="mdi-credit-card-outline"
              size="small"
              variant="tonal"
              @click="$router.push(`/patient/checkout/${appointment.id}`)"
            >
              Ir a pagar
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
