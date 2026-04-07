<script setup lang="ts">
import { FetchError } from 'ofetch'

import type {
  PrivacyIncident,
  PrivacyIncidentCreatePayload,
} from '~/types/privacy'

definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_validation', 'admin_support', 'admin_moderation', 'admin_privacy'],
})

const {
  getAdminPrivacyIncidents,
  createAdminPrivacyIncident,
  assignAdminPrivacyIncident,
  containAdminPrivacyIncident,
  resolveAdminPrivacyIncident,
  dismissAdminPrivacyIncident,
} = useApi()

const incidents = ref<PrivacyIncident[]>([])
const loading = ref(false)
const submitting = ref(false)
const actionSubmitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const filters = reactive({
  status_filter: '',
  severity: '',
})

const incidentForm = reactive<PrivacyIncidentCreatePayload>({
  incident_type: '',
  severity: 'medium',
  description: '',
  affected_resource_type: '',
  affected_resource_id: '',
})

const severityOptions = ['low', 'medium', 'high', 'critical']
const statusOptions = ['open', 'assigned', 'contained', 'resolved', 'dismissed']

const actionDialog = ref(false)
const actionType = ref<'assign' | 'contain' | 'resolve' | 'dismiss' | null>(null)
const selectedIncident = ref<PrivacyIncident | null>(null)

const actionForm = reactive({
  admin_id: '',
  summary: '',
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

function resetMessages() {
  errorMessage.value = ''
  successMessage.value = ''
}

async function loadIncidents() {
  loading.value = true
  resetMessages()

  try {
    incidents.value = await getAdminPrivacyIncidents({
      status_filter: filters.status_filter || undefined,
      severity: filters.severity || undefined,
    })
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudieron cargar incidentes.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado cargando incidentes.'
    }
    incidents.value = []
  }
  finally {
    loading.value = false
  }
}

async function handleCreateIncident() {
  submitting.value = true
  resetMessages()

  try {
    await createAdminPrivacyIncident({
      incident_type: incidentForm.incident_type.trim(),
      severity: incidentForm.severity.trim(),
      description: incidentForm.description.trim(),
      affected_resource_type: incidentForm.affected_resource_type?.trim() || null,
      affected_resource_id: incidentForm.affected_resource_id?.trim() || null,
    })

    successMessage.value = 'Incidente creado correctamente.'
    incidentForm.incident_type = ''
    incidentForm.severity = 'medium'
    incidentForm.description = ''
    incidentForm.affected_resource_type = ''
    incidentForm.affected_resource_id = ''
    await loadIncidents()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo crear el incidente.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado creando el incidente.'
    }
  }
  finally {
    submitting.value = false
  }
}

function openAction(kind: 'assign' | 'contain' | 'resolve' | 'dismiss', incident: PrivacyIncident) {
  selectedIncident.value = incident
  actionType.value = kind
  actionForm.admin_id = ''
  actionForm.summary = ''
  actionDialog.value = true
}

async function handleAction() {
  if (!selectedIncident.value || !actionType.value) {
    return
  }

  actionSubmitting.value = true
  resetMessages()

  try {
    if (actionType.value === 'assign') {
      await assignAdminPrivacyIncident(selectedIncident.value.id, {
        admin_id: actionForm.admin_id.trim(),
      })
      successMessage.value = 'Incidente asignado correctamente.'
    }

    if (actionType.value === 'contain') {
      await containAdminPrivacyIncident(selectedIncident.value.id)
      successMessage.value = 'Incidente contenido correctamente.'
    }

    if (actionType.value === 'resolve') {
      await resolveAdminPrivacyIncident(selectedIncident.value.id, {
        summary: actionForm.summary.trim(),
      })
      successMessage.value = 'Incidente resuelto correctamente.'
    }

    if (actionType.value === 'dismiss') {
      await dismissAdminPrivacyIncident(selectedIncident.value.id, {
        summary: actionForm.summary.trim(),
      })
      successMessage.value = 'Incidente descartado correctamente.'
    }

    actionDialog.value = false
    selectedIncident.value = null
    actionType.value = null
    await loadIncidents()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo ejecutar la accion.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado ejecutando la accion.'
    }
  }
  finally {
    actionSubmitting.value = false
  }
}

function clearFilters() {
  filters.status_filter = ''
  filters.severity = ''
  loadIncidents()
}

onMounted(() => {
  loadIncidents()
})
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <div class="d-flex justify-space-between align-center flex-wrap ga-3">
      <div>
        <h2 class="text-h5">Incidentes</h2>
        <p class="text-body-2 text-medium-emphasis mb-0">
          Registro, seguimiento y cierre de incidentes de privacidad.
        </p>
      </div>

      <v-btn
        :loading="loading"
        prepend-icon="mdi-refresh"
        variant="outlined"
        @click="loadIncidents"
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

    <v-alert
      v-if="successMessage"
      type="success"
      variant="tonal"
    >
      {{ successMessage }}
    </v-alert>

    <v-card rounded="xl">
      <v-card-item>
        <v-card-title>Nuevo incidente</v-card-title>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="incidentForm.incident_type"
              label="Incident type"
              prepend-inner-icon="mdi-alert-circle-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-select
              v-model="incidentForm.severity"
              :items="severityOptions"
              label="Severity"
              prepend-inner-icon="mdi-alert-decagram-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-text-field
              v-model="incidentForm.affected_resource_type"
              label="Affected resource type"
              prepend-inner-icon="mdi-file-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-text-field
              v-model="incidentForm.affected_resource_id"
              label="Affected resource id"
              prepend-inner-icon="mdi-identifier"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12">
            <v-textarea
              v-model="incidentForm.description"
              auto-grow
              label="Descripcion"
              prepend-inner-icon="mdi-text-box-outline"
              rows="2"
              variant="outlined"
            />
          </v-col>
        </v-row>

        <div class="d-flex justify-end">
          <v-btn
            :loading="submitting"
            color="primary"
            prepend-icon="mdi-content-save-outline"
            @click="handleCreateIncident"
          >
            Crear incidente
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <v-card rounded="xl">
      <v-card-item>
        <v-card-title>Filtros</v-card-title>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.status_filter"
              :items="['', ...statusOptions]"
              label="Status"
              prepend-inner-icon="mdi-filter-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-select
              v-model="filters.severity"
              :items="['', ...severityOptions]"
              label="Severity"
              prepend-inner-icon="mdi-filter-outline"
              variant="outlined"
            />
          </v-col>
        </v-row>

        <div class="d-flex flex-wrap ga-3">
          <v-btn
            :loading="loading"
            color="primary"
            prepend-icon="mdi-magnify"
            @click="loadIncidents"
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
      v-else-if="!incidents.length"
      type="info"
      variant="tonal"
    >
      No existen incidentes para los filtros seleccionados.
    </v-alert>

    <v-row v-else>
      <v-col
        v-for="incident in incidents"
        :key="incident.id"
        cols="12"
        md="6"
      >
        <v-card class="h-100" rounded="xl">
          <v-card-item>
            <template #append>
              <v-chip color="primary" variant="tonal">
                {{ incident.status }}
              </v-chip>
            </template>

            <v-card-title>{{ incident.incident_code }}</v-card-title>
            <v-card-subtitle>{{ incident.incident_type }} · {{ incident.severity }}</v-card-subtitle>
          </v-card-item>

          <v-card-text class="d-flex flex-column ga-2">
            <div>
              <div class="text-caption text-medium-emphasis">Detectado</div>
              <div class="text-body-2">{{ formatDateTime(incident.detected_at) }}</div>
            </div>

            <div>
              <div class="text-caption text-medium-emphasis">Descripcion</div>
              <div class="text-body-2">{{ incident.description }}</div>
            </div>

            <div>
              <div class="text-caption text-medium-emphasis">Recurso afectado</div>
              <div class="text-body-2">
                {{ incident.affected_resource_type || 'No definido' }} · {{ incident.affected_resource_id || 'No definido' }}
              </div>
            </div>

            <div>
              <div class="text-caption text-medium-emphasis">Asignado a</div>
              <div class="text-body-2">{{ incident.assigned_admin_id || 'No asignado' }}</div>
            </div>

            <div v-if="incident.resolution_summary">
              <div class="text-caption text-medium-emphasis">Resolucion</div>
              <div class="text-body-2">{{ incident.resolution_summary }}</div>
            </div>
          </v-card-text>

          <v-card-actions class="d-flex flex-wrap ga-2">
            <v-btn
              color="primary"
              prepend-icon="mdi-account-plus-outline"
              variant="tonal"
              @click="openAction('assign', incident)"
            >
              Asignar
            </v-btn>

            <v-btn
              color="warning"
              prepend-icon="mdi-shield-alert-outline"
              variant="tonal"
              @click="openAction('contain', incident)"
            >
              Contener
            </v-btn>

            <v-btn
              color="success"
              prepend-icon="mdi-check-circle-outline"
              variant="tonal"
              @click="openAction('resolve', incident)"
            >
              Resolver
            </v-btn>

            <v-btn
              color="error"
              prepend-icon="mdi-close-circle-outline"
              variant="tonal"
              @click="openAction('dismiss', incident)"
            >
              Descartar
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog
      v-model="actionDialog"
      max-width="640"
    >
      <v-card rounded="xl">
        <v-card-item>
          <v-card-title>Accion sobre incidente</v-card-title>
        </v-card-item>

        <v-card-text class="d-flex flex-column ga-4">
          <div class="text-body-2">
            Tipo de accion: {{ actionType }}
          </div>

          <v-text-field
            v-if="actionType === 'assign'"
            v-model="actionForm.admin_id"
            label="Admin id"
            prepend-inner-icon="mdi-account-outline"
            variant="outlined"
          />

          <v-textarea
            v-if="actionType === 'resolve' || actionType === 'dismiss'"
            v-model="actionForm.summary"
            auto-grow
            label="Summary"
            prepend-inner-icon="mdi-text-box-outline"
            rows="2"
            variant="outlined"
          />
        </v-card-text>

        <v-card-actions class="justify-end">
          <v-btn
            variant="text"
            @click="actionDialog = false"
          >
            Cancelar
          </v-btn>

          <v-btn
            :loading="actionSubmitting"
            color="primary"
            @click="handleAction"
          >
            Confirmar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
