<script setup lang="ts">
import type { AdminVerificationRequest } from '~/types/verification'

definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_validation', 'admin_support'],
})

const { apiFetch } = useApi()

const requests = ref<AdminVerificationRequest[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const statusColors: Record<string, string> = {
  submitted: 'blue',
  under_review: 'orange',
  approved: 'green',
  rejected: 'red',
  needs_correction: 'amber',
  suspended: 'grey',
}

async function loadRequests() {
  loading.value = true
  error.value = null
  try {
    requests.value = await apiFetch<AdminVerificationRequest[]>('/admin/verification-requests', { method: 'GET' })
  }
  catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error al cargar solicitudes'
  }
  finally {
    loading.value = false
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('es-EC', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  loadRequests()
})
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h2 class="text-h5 font-weight-bold">Validación de Profesionales</h2>
        <p class="text-body-2 text-medium-emphasis">
          Revisa y valida los documentos de los profesionales
        </p>
      </div>
      <v-btn color="primary" variant="tonal" :loading="loading" @click="loadRequests">
        <v-icon start>mdi-refresh</v-icon>
        Actualizar
      </v-btn>
    </div>

    <v-alert v-if="error" type="error" class="mb-4" closable @click:close="error = null">
      {{ error }}
    </v-alert>

    <v-card v-if="loading && requests.length === 0" class="text-center pa-8">
      <v-progress-circular indeterminate color="primary" />
      <p class="mt-4 text-body-2">Cargando solicitudes...</p>
    </v-card>

    <v-card v-else-if="requests.length === 0" class="text-center pa-8">
      <v-icon size="64" color="grey">mdi-clipboard-check-outline</v-icon>
      <p class="text-h6 mt-4">No hay solicitudes pendientes</p>
      <p class="text-body-2 text-medium-emphasis">
        Las solicitudes de verificación aparecerán aquí
      </p>
    </v-card>

    <v-row v-else>
      <v-col v-for="req in requests" :key="req.id" cols="12" md="6" lg="4">
        <v-card rounded="xl" class="h-100">
          <v-card-item>
            <template #prepend>
              <v-avatar :color="statusColors[req.status] ?? 'grey'" size="40">
                <v-icon color="white">
                  {{
                    req.status === 'approved' ? 'mdi-check-circle'
                      : req.status === 'rejected' ? 'mdi-close-circle'
                      : req.status === 'under_review' ? 'mdi-clock-outline'
                      : 'mdi-clipboard-text-outline'
                  }}
                </v-icon>
              </v-avatar>
            </template>
            <v-card-title class="text-body-1 font-weight-bold">
              {{ req.professional_display_name ?? 'Sin nombre' }}
            </v-card-title>
            <v-card-subtitle>
              {{ req.professional_email ?? 'Sin email' }}
            </v-card-subtitle>
          </v-card-item>

          <v-card-text>
            <div class="d-flex flex-wrap ga-2 mt-2">
              <v-chip
                :color="statusColors[req.status]"
                variant="flat"
                size="small"
              >
                {{ req.status.replace('_', ' ') }}
              </v-chip>
              <v-chip variant="outlined" size="small">
                <v-icon start size="small">mdi-file-document</v-icon>
                {{ req.document_count }} docs
              </v-chip>
            </div>

            <v-divider class="my-3" />

            <div class="d-flex justify-space-between text-body-2">
              <span class="text-medium-emphasis">Aprobados:</span>
              <span class="text-success font-weight-bold">{{ req.approved_count }}</span>
            </div>
            <div class="d-flex justify-space-between text-body-2">
              <span class="text-medium-emphasis">Pendientes:</span>
              <span class="text-warning font-weight-bold">{{ req.pending_count }}</span>
            </div>
            <div class="d-flex justify-space-between text-body-2">
              <span class="text-medium-emphasis">Rechazados:</span>
              <span class="text-error font-weight-bold">{{ req.rejected_count }}</span>
            </div>

            <p class="text-caption text-medium-emphasis mt-3">
              Enviado: {{ formatDate(req.submitted_at) }}
            </p>
          </v-card-text>

          <v-card-actions>
            <v-btn
              :to="`/admin/verification/${req.id}`"
              color="primary"
              variant="tonal"
              block
            >
              Revisar
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
