<script setup lang="ts">
import { FetchError } from 'ofetch'

import type {
  ExceptionalAccessRequestCreatePayload,
  ExceptionalAccessRequestResponse,
} from '~/types/privacy'

definePageMeta({
  layout: 'professional',
  middleware: ['auth', 'role'],
  roles: ['professional'],
})

const {
  createExceptionalAccessRequest,
  getProfessionalExceptionalAccessRequests,
} = useApi()

const requests = ref<ExceptionalAccessRequestResponse[]>([])
const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const form = reactive<ExceptionalAccessRequestCreatePayload>({
  patient_id: '',
  target_user_id: '',
  resource_type: 'clinical_note',
  resource_id: '',
  scope_type: 'single_resource',
  justification: '',
  business_basis: '',
  requested_minutes: 30,
})

const resourceTypeOptions = [
  'clinical_note',
  'prescription',
  'care_instruction',
  'clinical_file',
  'teleconsultation',
]

const scopeTypeOptions = [
  'single_resource',
  'appointment_scope',
  'patient_scope',
]

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

async function loadRequests() {
  loading.value = true
  resetMessages()

  try {
    requests.value = await getProfessionalExceptionalAccessRequests()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudieron consultar las solicitudes.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado al consultar solicitudes.'
    }
    requests.value = []
  }
  finally {
    loading.value = false
  }
}

async function handleCreateRequest() {
  submitting.value = true
  resetMessages()

  try {
    await createExceptionalAccessRequest({
      patient_id: form.patient_id?.trim() || null,
      target_user_id: form.target_user_id?.trim() || null,
      resource_type: form.resource_type?.trim() || '',
      resource_id: form.resource_id?.trim() || null,
      scope_type: form.scope_type?.trim() || '',
      justification: form.justification?.trim() || '',
      business_basis: form.business_basis?.trim() || null,
      requested_minutes: Number(form.requested_minutes) || 0,
    })

    successMessage.value = 'Solicitud creada correctamente.'
    form.patient_id = ''
    form.target_user_id = ''
    form.resource_id = ''
    form.justification = ''
    form.business_basis = ''
    form.requested_minutes = 30

    await loadRequests()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo crear la solicitud.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado al crear la solicitud.'
    }
  }
  finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadRequests()
})
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <div class="d-flex justify-space-between align-center flex-wrap ga-3">
      <div>
        <h2 class="text-h5">Acceso excepcional</h2>
        <p class="text-body-2 text-medium-emphasis mb-0">
          El profesional crea solicitudes y revisa el estado de sus propias peticiones.
        </p>
      </div>

      <v-btn
        :loading="loading"
        prepend-icon="mdi-refresh"
        variant="outlined"
        @click="loadRequests"
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
        <v-card-title>Nueva solicitud</v-card-title>
        <v-card-subtitle>
          La justificacion y los minutos solicitados son obligatorios.
        </v-card-subtitle>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="form.patient_id"
              label="Patient id"
              prepend-inner-icon="mdi-account"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-text-field
              v-model="form.target_user_id"
              label="Target user id"
              prepend-inner-icon="mdi-account-arrow-right-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-select
              v-model="form.resource_type"
              :items="resourceTypeOptions"
              label="Resource type"
              prepend-inner-icon="mdi-file-lock-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-text-field
              v-model="form.resource_id"
              label="Resource id"
              prepend-inner-icon="mdi-identifier"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-select
              v-model="form.scope_type"
              :items="scopeTypeOptions"
              label="Scope type"
              prepend-inner-icon="mdi-sitemap-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-text-field
              v-model.number="form.requested_minutes"
              label="Requested minutes"
              min="1"
              prepend-inner-icon="mdi-timer-outline"
              type="number"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-text-field
              v-model="form.business_basis"
              label="Business basis"
              prepend-inner-icon="mdi-briefcase-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12">
            <v-textarea
              v-model="form.justification"
              auto-grow
              label="Justificacion"
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
            prepend-icon="mdi-send-outline"
            @click="handleCreateRequest"
          >
            Crear solicitud
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <v-card rounded="xl">
      <v-card-item>
        <v-card-title>Solicitudes propias</v-card-title>
      </v-card-item>

      <v-card-text>
        <v-skeleton-loader
          v-if="loading"
          rounded="xl"
          type="article, article, article"
        />

        <v-alert
          v-else-if="!requests.length"
          type="info"
          variant="tonal"
        >
          No existen solicitudes creadas por este profesional.
        </v-alert>

        <v-row v-else>
          <v-col
            v-for="request in requests"
            :key="request.id"
            cols="12"
            md="6"
          >
            <v-card class="h-100" rounded="xl">
              <v-card-item>
                <template #append>
                  <v-chip color="primary" variant="tonal">
                    {{ request.status }}
                  </v-chip>
                </template>

                <v-card-title>{{ request.resource_type }}</v-card-title>
                <v-card-subtitle>{{ request.scope_type }}</v-card-subtitle>
              </v-card-item>

              <v-card-text class="d-flex flex-column ga-2">
                <div>
                  <div class="text-caption text-medium-emphasis">Creada</div>
                  <div class="text-body-2">{{ formatDateTime(request.created_at) }}</div>
                </div>

                <div>
                  <div class="text-caption text-medium-emphasis">Minutos solicitados</div>
                  <div class="text-body-2">{{ request.requested_minutes }}</div>
                </div>

                <div>
                  <div class="text-caption text-medium-emphasis">Requiere autorizacion del paciente</div>
                  <div class="text-body-2">{{ request.requires_patient_authorization ? 'Si' : 'No' }}</div>
                </div>

                <div v-if="request.patient_id">
                  <div class="text-caption text-medium-emphasis">Patient id</div>
                  <div class="text-body-2">{{ request.patient_id }}</div>
                </div>

                <div v-if="request.resource_id">
                  <div class="text-caption text-medium-emphasis">Resource id</div>
                  <div class="text-body-2">{{ request.resource_id }}</div>
                </div>

                <div>
                  <div class="text-caption text-medium-emphasis">Justificacion</div>
                  <div class="text-body-2">{{ request.justification }}</div>
                </div>

                <div v-if="request.approved_at || request.expires_at">
                  <div class="text-caption text-medium-emphasis">Ventana aprobada</div>
                  <div class="text-body-2">
                    {{ formatDateTime(request.approved_at) }} · {{ formatDateTime(request.expires_at) }}
                  </div>
                </div>

                <div v-if="request.rejection_reason">
                  <div class="text-caption text-medium-emphasis">Rechazo</div>
                  <div class="text-body-2">{{ request.rejection_reason }}</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>
