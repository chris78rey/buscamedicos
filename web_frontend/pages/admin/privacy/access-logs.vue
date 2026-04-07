<script setup lang="ts">
import { FetchError } from 'ofetch'

import type { ClinicalAccessLog } from '~/types/privacy'

definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_validation', 'admin_support', 'admin_moderation', 'admin_privacy'],
})

const {
  getAdminPrivacyAccessLogs,
  exportAdminPrivacyAccessLogsMeta,
} = useApi()

const logs = ref<ClinicalAccessLog[]>([])
const loading = ref(false)
const exporting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const filters = reactive({
  actor_user_id: '',
  resource_type: '',
  from_date: '',
  to_date: '',
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
  successMessage.value = ''

  try {
    logs.value = await getAdminPrivacyAccessLogs({
      actor_user_id: filters.actor_user_id || undefined,
      resource_type: filters.resource_type || undefined,
      from_date: filters.from_date || undefined,
      to_date: filters.to_date || undefined,
    })
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudieron cargar los logs.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado cargando logs.'
    }
    logs.value = []
  }
  finally {
    loading.value = false
  }
}

function downloadJson(filename: string, data: unknown) {
  if (typeof window === 'undefined') {
    return
  }

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

async function handleExport() {
  exporting.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const exported = await exportAdminPrivacyAccessLogsMeta({
      actor_user_id: filters.actor_user_id || undefined,
      resource_type: filters.resource_type || undefined,
      from_date: filters.from_date || undefined,
      to_date: filters.to_date || undefined,
    })

    downloadJson('admin_privacy_access_logs_meta.json', exported)
    successMessage.value = 'Exportacion metadata generada correctamente.'
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo exportar metadata.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado exportando metadata.'
    }
  }
  finally {
    exporting.value = false
  }
}

function clearFilters() {
  filters.actor_user_id = ''
  filters.resource_type = ''
  filters.from_date = ''
  filters.to_date = ''
  loadLogs()
}

onMounted(() => {
  loadLogs()
})
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <div class="d-flex justify-space-between align-center flex-wrap ga-3">
      <div>
        <h2 class="text-h5">Logs administrativos</h2>
        <p class="text-body-2 text-medium-emphasis mb-0">
          Vista administrativa de metadatos de acceso. No expone contenido clinico.
        </p>
      </div>

      <div class="d-flex flex-wrap ga-3">
        <v-btn
          :loading="loading"
          prepend-icon="mdi-refresh"
          variant="outlined"
          @click="loadLogs"
        >
          Recargar
        </v-btn>

        <v-btn
          :loading="exporting"
          color="primary"
          prepend-icon="mdi-download"
          variant="tonal"
          @click="handleExport"
        >
          Export meta
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

    <v-alert
      v-if="successMessage"
      type="success"
      variant="tonal"
    >
      {{ successMessage }}
    </v-alert>

    <v-card rounded="xl">
      <v-card-item>
        <v-card-title>Filtros</v-card-title>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.actor_user_id"
              label="Actor user id"
              prepend-inner-icon="mdi-account-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.resource_type"
              label="Resource type"
              prepend-inner-icon="mdi-file-search-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.from_date"
              label="Desde"
              type="datetime-local"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.to_date"
              label="Hasta"
              type="datetime-local"
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
      No existen logs para los filtros seleccionados.
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
              <div class="text-caption text-medium-emphasis">Paciente</div>
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
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
