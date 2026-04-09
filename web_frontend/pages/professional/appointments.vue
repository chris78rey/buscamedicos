<script setup lang="ts">
import { useApi } from '~/composables/useApi'
import type { AppointmentSummary } from '~/types/appointment'

definePageMeta({
  layout: 'professional',
  middleware: ['auth', 'role'],
  roles: ['professional'],
})

const { getProfessionalAppointments, confirmAppointment, cancelAppointment, completeAppointment } = useApi()

const appointments = ref<AppointmentSummary[]>([])
const loading = ref(true)
const tab = ref(0)
const error = ref('')

const fetchAppointments = async () => {
  loading.value = true
  error.value = ''
  try {
    appointments.value = await getProfessionalAppointments()
  } catch (err: any) {
    error.value = 'No se pudieron cargar las citas. Por favor, reintente.'
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleConfirm = async (id: string) => {
  try {
    await confirmAppointment(id)
    await fetchAppointments()
  } catch (err) {
    alert('Error al confirmar la cita.')
  }
}

const handleCancel = async (id: string) => {
  const reason = prompt('Motivo de la cancelación (opcional):')
  if (reason === null) return
  try {
    await cancelAppointment(id, reason)
    await fetchAppointments()
  } catch (err) {
    alert('Error al cancelar la cita.')
  }
}

const handleComplete = async (id: string) => {
  if (!confirm('¿Seguro que desea marcar esta cita como completada?')) return
  try {
    await completeAppointment(id)
    await fetchAppointments()
  } catch (err) {
    alert('Error al completar la cita.')
  }
}

onMounted(fetchAppointments)

const filteredAppointments = computed(() => {
  if (tab.value === 0) {
    return appointments.value.filter(a => ['pending_confirmation', 'confirmed'].includes(a.status))
  } else if (tab.value === 1) {
    return appointments.value.filter(a => a.status === 'completed')
  } else {
    return appointments.value.filter(a => a.status.startsWith('cancelled') || a.status.startsWith('no_show'))
  }
})

function getStatusColor(status: string) {
  switch (status) {
    case 'confirmed': return 'success'
    case 'pending_confirmation': return 'warning'
    case 'completed': return 'info'
    case 'cancelled_by_patient':
    case 'cancelled_by_professional': return 'error'
    default: return 'grey'
  }
}

function getStatusText(status: string) {
  switch (status) {
    case 'confirmed': return 'Confirmada'
    case 'pending_confirmation': return 'Pendiente'
    case 'completed': return 'Completada'
    case 'cancelled_by_patient': return 'Cancelada (Paciente)'
    case 'cancelled_by_professional': return 'Cancelada (Usted)'
    case 'no_show_patient': return 'No asistió (Paciente)'
    case 'no_show_professional': return 'No asistió (Usted)'
    default: return status
  }
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleDateString('es-EC', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}

function formatTime(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleTimeString('es-EC', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <v-container>
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold mb-1">Agenda Profesional</h1>
        <p class="text-subtitle-1 text-medium-emphasis">Gestiona tus próximas citas y revisa tu historial clínico.</p>
      </div>
      <v-spacer></v-spacer>
      <v-btn
        icon="mdi-refresh"
        variant="tonal"
        :loading="loading"
        @click="fetchAppointments"
      ></v-btn>
    </div>

    <v-tabs v-model="tab" color="primary" align-tabs="start" class="mb-6">
      <v-tab :value="0">Activas</v-tab>
      <v-tab :value="1">Completadas</v-tab>
      <v-tab :value="2">Historial / Cancelaciones</v-tab>
    </v-tabs>

    <div v-if="loading" class="text-center py-12">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </div>

    <div v-else-if="error" class="mb-6">
      <v-alert type="error" variant="tonal" closable>
        {{ error }}
      </v-alert>
    </div>

    <div v-else-if="filteredAppointments.length === 0" class="text-center py-12">
      <v-icon size="64" color="grey-lighten-1">mdi-calendar-blank</v-icon>
      <p class="text-h6 text-medium-emphasis mt-4">No hay citas en esta sección.</p>
    </div>

    <v-row v-else>
      <v-col v-for="apt in filteredAppointments" :key="apt.id" cols="12">
        <v-card rounded="xl" elevation="2" class="mb-2">
          <v-row no-gutters>
            <v-col cols="12" md="3" class="bg-blue-lighten-5 d-flex flex-column justify-center align-center py-4 px-2">
              <div class="text-h5 font-weight-black text-primary">{{ formatTime(apt.scheduled_start) }}</div>
              <div class="text-caption text-uppercase font-weight-bold">{{ formatDate(apt.scheduled_start) }}</div>
            </v-col>
            <v-col cols="12" md="9">
              <v-card-item>
                <template v-slot:prepend>
                   <v-avatar color="primary" rounded="lg">
                     <v-icon color="white">mdi-account</v-icon>
                   </v-avatar>
                </template>
                <v-card-title class="d-flex align-center">
                  Cita #{{ apt.public_code || apt.id.slice(0, 8) }}
                  <v-spacer></v-spacer>
                  <v-chip :color="getStatusColor(apt.status)" size="small" variant="flat" class="text-uppercase font-weight-bold">
                    {{ getStatusText(apt.status) }}
                  </v-chip>
                </v-card-title>
                <v-card-subtitle>
                  Modalidad: {{ apt.modality_code === 'teleconsulta' ? '💻 Teleconsulta' : '🏥 Presencial' }}
                </v-card-subtitle>
              </v-card-item>

              <v-card-text v-if="apt.patient_note" class="text-body-2 italic py-0">
                <v-icon size="small" class="mr-1">mdi-note-text-outline</v-icon>
                "{{ apt.patient_note }}"
              </v-card-text>

              <v-card-actions class="pa-4 pt-2">
                <v-btn
                  v-if="apt.status === 'pending_confirmation'"
                  color="success"
                  variant="flat"
                  rounded="lg"
                  prepend-icon="mdi-check"
                  @click="handleConfirm(apt.id)"
                >
                  Confirmar
                </v-btn>

                <v-btn
                  v-if="apt.status === 'confirmed'"
                  color="info"
                  variant="tonal"
                  rounded="lg"
                  prepend-icon="mdi-video"
                  :to="`/professional/teleconsultation/${apt.id}`"
                  :disabled="apt.modality_code !== 'teleconsulta'"
                >
                  Iniciar Consulta
                </v-btn>

                <v-spacer></v-spacer>

                <v-btn
                  v-if="apt.status === 'confirmed'"
                  color="success"
                  variant="outlined"
                  rounded="lg"
                  @click="handleComplete(apt.id)"
                >
                   Finalizar
                </v-btn>

                <v-btn
                  v-if="['pending_confirmation', 'confirmed'].includes(apt.status)"
                  color="error"
                  variant="text"
                  rounded="lg"
                  @click="handleCancel(apt.id)"
                >
                  Cancelar
                </v-btn>

                <v-btn
                  variant="plain"
                  rounded="lg"
                  icon="mdi-dots-vertical"
                ></v-btn>
              </v-card-actions>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.v-card {
  transition: transform 0.2s ease-in-out;
}
.v-card:hover {
  transform: translateY(-2px);
}
</style>
