<script setup lang="ts">
import { FetchError } from 'ofetch'

import type { ClinicalAccessLog } from '~/types/privacy'

definePageMeta({
  layout: 'patient',
  middleware: ['auth', 'role'],
  roles: ['patient'],
})

const { getPatientAccessLogs } = useApi()

const logs = ref<ClinicalAccessLog[]>([])
const loading = ref(false)
const errorMessage = ref('')

function formatDateTime(value?: string | null) {
  if (!value) {
    return 'No disponible'
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

async function loadLogs() {
  loading.value = true
  errorMessage.value = ''

  try {
    logs.value = await getPatientAccessLogs()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo consultar la trazabilidad.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado al consultar la trazabilidad.'
    }
    logs.value = []
  }
  finally {
    loading.value = false
  }
}

onMounted(() => {
  loadLogs()
})
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <div class="d-flex justify-space-between align-center flex-wrap ga-3">
      <div>
        <h2 class="text-h5">Logs de acceso</h2>
        <p class="text-body-2 text-medium-emphasis mb-0">
          El paciente ve su propia trazabilidad de accesos registrada por el backend.
        </p>
      </div>

      <v-btn
        :loading="loading"
        prepend-icon="mdi-refresh"
        variant="outlined"
        @click="loadLogs"
      >
        Recargar
      </v-btn>
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
      v-else-if="!logs.length"
      type="info"
      variant="tonal"
    >
      No existen logs de acceso visibles.
    </v-alert>

    <v-row v-else>
      <v-col
        v-for="log in logs"
        :key="log.id"
        cols="12"
        md="6"
      >
        <v-card class="h-100" rounded="xl">
          <v-card-item>
            <template #append>
              <v-chip
                :color="log.decision === 'allowed' ? 'success' : 'error'"
                variant="tonal"
              >
                {{ log.decision }}
              </v-chip>
            </template>

            <v-card-title>{{ log.resource_type }}</v-card-title>
            <v-card-subtitle>{{ log.action }}</v-card-subtitle>
          </v-card-item>

          <v-card-text class="d-flex flex-column ga-2">
            <div>
              <div class="text-caption text-medium-emphasis">Fecha</div>
              <div class="text-body-2">{{ formatDateTime(log.created_at) }}</div>
            </div>

            <div>
              <div class="text-caption text-medium-emphasis">Modo de acceso</div>
              <div class="text-body-2">{{ log.access_mode }}</div>
            </div>

            <div>
              <div class="text-caption text-medium-emphasis">Actor</div>
              <div class="text-body-2">{{ log.actor_role_code }} · {{ log.actor_user_id }}</div>
            </div>

            <div v-if="log.resource_id">
              <div class="text-caption text-medium-emphasis">Resource id</div>
              <div class="text-body-2">{{ log.resource_id }}</div>
            </div>

            <div v-if="log.exceptional_access_request_id">
              <div class="text-caption text-medium-emphasis">Exceptional request</div>
              <div class="text-body-2">{{ log.exceptional_access_request_id }}</div>
            </div>

            <div v-if="log.justification">
              <div class="text-caption text-medium-emphasis">Justificacion</div>
              <div class="text-body-2">{{ log.justification }}</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
