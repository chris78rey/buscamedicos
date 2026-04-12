<script setup lang="ts">
import { FetchError } from 'ofetch'

import type { ClinicalAccessLog } from '~/types/privacy'

definePageMeta({
  layout: 'default',
  middleware: ['auth', 'role'],
  roles: ['privacy_auditor'],
})

const { getPrivacyAuditorAccessLogs } = useApi()

const logs = ref<ClinicalAccessLog[]>([])
const loading = ref(false)
const errorMessage = ref('')

const filters = reactive({
  actor_user_id: '',
  patient_id: '',
  resource_type: '',
  from_date: '',
  to_date: '',
  limit: 100,
})

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
    const response = await getPrivacyAuditorAccessLogs({
      actor_user_id: filters.actor_user_id || undefined,
      patient_id: filters.patient_id || undefined,
      resource_type: filters.resource_type || undefined,
      from_date: filters.from_date || undefined,
      to_date: filters.to_date || undefined,
      limit: filters.limit || 100,
    })

    logs.value = response.logs
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudieron consultar los logs de auditoria.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado al consultar auditoria.'
    }
    logs.value = []
  }
  finally {
    loading.value = false
  }
}

function clearFilters() {
  filters.actor_user_id = ''
  filters.patient_id = ''
  filters.resource_type = ''
  filters.from_date = ''
  filters.to_date = ''
  filters.limit = 100
  loadLogs()
}

onMounted(() => {
  loadLogs()
})
</script>

<template>
  <v-container class="py-10">
    <div class="d-flex flex-column ga-6">
      <div class="d-flex justify-space-between align-center flex-wrap ga-3">
        <div>
          <h2 class="text-h5">Auditoria de accesos</h2>
          <p class="text-body-2 text-medium-emphasis mb-0">
            Vista de metadatos de trazabilidad para el rol privacy_auditor.
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

      <v-card rounded="xl">
        <v-card-item>
          <v-card-title>Filtros</v-card-title>
        </v-card-item>

        <v-card-text>
          <v-row>
            <v-col cols="12" md="2">
              <v-text-field
                v-model="filters.actor_user_id"
                label="Actor user id"
                prepend-inner-icon="mdi-account-outline"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" md="2">
              <v-text-field
                v-model="filters.patient_id"
                label="Patient id"
                prepend-inner-icon="mdi-account-heart-outline"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" md="2">
              <v-text-field
                v-model="filters.resource_type"
                label="Resource type"
                prepend-inner-icon="mdi-file-search-outline"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" md="2">
              <v-text-field
                v-model="filters.from_date"
                label="Desde"
                type="datetime-local"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" md="2">
              <v-text-field
                v-model="filters.to_date"
                label="Hasta"
                type="datetime-local"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" md="2">
              <v-text-field
                v-model.number="filters.limit"
                label="Limit"
                min="1"
                max="1000"
                type="number"
                variant="outlined"
              />
            </v-col>
          </v-row>

          <div class="d-flex flex-wrap ga-3">
            <v-btn
              :loading="loading"
              color="primary"
              prepend-icon="mdi-magnify"
              @click="loadLogs"
            >
              Buscar
            </v-btn>

            <v-btn
              prepend-icon="mdi-filter-off-outline"
              variant="tonal"
              @click="clearFilters"
            >
              Limpiar
            </v-btn>
          </div>
        </v-card-text>
      </v-card>

      <v-skeleton-loader
        v-if="loading"
        rounded="xl"
        type="article, article, article"
      />

      <v-alert
        v-else-if="!logs.length"
        type="info"
        variant="tonal"
      >
        No existen resultados para los filtros seleccionados.
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
                <div class="text-caption text-medium-emphasis">Actor</div>
                <div class="text-body-2">{{ log.actor_role_code }} · {{ log.actor_user_id }}</div>
              </div>

              <div>
                <div class="text-caption text-medium-emphasis">Patient id</div>
                <div class="text-body-2">{{ log.patient_id || 'No aplica' }}</div>
              </div>

              <div>
                <div class="text-caption text-medium-emphasis">Modo</div>
                <div class="text-body-2">{{ log.access_mode }}</div>
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
  </v-container>
</template>
