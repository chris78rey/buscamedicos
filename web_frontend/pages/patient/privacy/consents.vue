<script setup lang="ts">
import { FetchError } from 'ofetch'

import type {
  ConsentCreatePayload,
  ConsentResponse,
  PrivacyPolicyVersion,
} from '~/types/privacy'

definePageMeta({
  layout: 'patient',
  middleware: ['auth', 'role'],
  roles: ['patient'],
})

const {
  createPatientConsent,
  getPatientConsents,
  getPatientPrivacyPolicies,
  revokePatientConsent,
} = useApi()

const consents = ref<ConsentResponse[]>([])
const policies = ref<PrivacyPolicyVersion[]>([])
const loading = ref(false)
const submitting = ref(false)
const revokingConsentId = ref<string | null>(null)
const errorMessage = ref('')
const successMessage = ref('')

const form = reactive<ConsentCreatePayload>({
  consent_type: 'privacy_policy_general',
  source: 'self_service_web',
  evidence_file_id: '',
  expires_at: '',
  notes: '',
})

const consentTypeOptions = [
  'privacy_policy_general',
  'exceptional_access_authorization',
  'teleconsultation_terms',
  'data_processing_authorization',
]

function formatDateTime(value?: string | null) {
  if (!value) {
    return 'No aplica'
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

async function loadData() {
  loading.value = true
  resetMessages()

  try {
    const [consentList, policyList] = await Promise.all([
      getPatientConsents(),
      getPatientPrivacyPolicies(),
    ])

    consents.value = consentList
    policies.value = policyList
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo cargar la informacion de privacidad.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado al cargar privacidad.'
    }
  }
  finally {
    loading.value = false
  }
}

async function handleCreateConsent() {
  submitting.value = true
  resetMessages()

  try {
    await createPatientConsent({
      consent_type: form.consent_type?.trim() || '',
      source: form.source?.trim() || '',
      evidence_file_id: form.evidence_file_id?.trim() || null,
      expires_at: form.expires_at?.trim() || null,
      notes: form.notes?.trim() || null,
    })

    successMessage.value = 'Consentimiento otorgado correctamente.'
    form.evidence_file_id = ''
    form.expires_at = ''
    form.notes = ''

    await loadData()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo otorgar el consentimiento.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado al otorgar el consentimiento.'
    }
  }
  finally {
    submitting.value = false
  }
}

async function handleRevoke(consentId: string) {
  revokingConsentId.value = consentId
  resetMessages()

  try {
    await revokePatientConsent(consentId)
    successMessage.value = 'Consentimiento revocado correctamente.'
    await loadData()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo revocar el consentimiento.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado al revocar el consentimiento.'
    }
  }
  finally {
    revokingConsentId.value = null
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <div class="d-flex justify-space-between align-center flex-wrap ga-3">
      <div>
        <h2 class="text-h5">Consentimientos</h2>
        <p class="text-body-2 text-medium-emphasis mb-0">
          Se listan consentimientos activos del paciente y las politicas activas publicadas.
        </p>
      </div>

      <v-btn
        :loading="loading"
        prepend-icon="mdi-refresh"
        variant="outlined"
        @click="loadData"
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
        <v-card-title>Otorgar consentimiento</v-card-title>
        <v-card-subtitle>
          El paciente genera consentimientos simples desde la web.
        </v-card-subtitle>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <v-combobox
              v-model="form.consent_type"
              :items="consentTypeOptions"
              label="Consent type"
              prepend-inner-icon="mdi-shield-check-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-text-field
              v-model="form.source"
              label="Source"
              prepend-inner-icon="mdi-source-branch"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-text-field
              v-model="form.expires_at"
              label="Expira en"
              prepend-inner-icon="mdi-calendar-clock"
              type="datetime-local"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="6">
            <v-text-field
              v-model="form.evidence_file_id"
              label="Evidence file id"
              prepend-inner-icon="mdi-file-document-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="6">
            <v-textarea
              v-model="form.notes"
              auto-grow
              label="Notas"
              prepend-inner-icon="mdi-note-text-outline"
              rows="1"
              variant="outlined"
            />
          </v-col>
        </v-row>

        <div class="d-flex justify-end">
          <v-btn
            :loading="submitting"
            color="primary"
            prepend-icon="mdi-check-circle-outline"
            @click="handleCreateConsent"
          >
            Guardar consentimiento
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <v-card rounded="xl">
      <v-card-item>
        <v-card-title>Consentimientos activos</v-card-title>
      </v-card-item>

      <v-card-text>
        <v-skeleton-loader
          v-if="loading"
          rounded="xl"
          type="article, article"
        />

        <v-alert
          v-else-if="!consents.length"
          type="info"
          variant="tonal"
        >
          No existen consentimientos activos.
        </v-alert>

        <v-row v-else>
          <v-col
            v-for="consent in consents"
            :key="consent.id"
            cols="12"
            md="6"
          >
            <v-card class="h-100" rounded="xl" variant="tonal">
              <v-card-item>
                <template #append>
                  <v-chip color="primary" variant="tonal">
                    {{ consent.status }}
                  </v-chip>
                </template>

                <v-card-title>{{ consent.consent_type }}</v-card-title>
                <v-card-subtitle>{{ consent.source }}</v-card-subtitle>
              </v-card-item>

              <v-card-text class="d-flex flex-column ga-2">
                <div>
                  <div class="text-caption text-medium-emphasis">Otorgado</div>
                  <div class="text-body-2">{{ formatDateTime(consent.granted_at) }}</div>
                </div>

                <div>
                  <div class="text-caption text-medium-emphasis">Expira</div>
                  <div class="text-body-2">{{ formatDateTime(consent.expires_at) }}</div>
                </div>

                <div v-if="consent.notes">
                  <div class="text-caption text-medium-emphasis">Notas</div>
                  <div class="text-body-2">{{ consent.notes }}</div>
                </div>
              </v-card-text>

              <v-card-actions>
                <v-btn
                  :loading="revokingConsentId === consent.id"
                  color="error"
                  prepend-icon="mdi-cancel"
                  variant="tonal"
                  @click="handleRevoke(consent.id)"
                >
                  Revocar
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card rounded="xl">
      <v-card-item>
        <v-card-title>Politicas activas</v-card-title>
      </v-card-item>

      <v-card-text>
        <v-alert
          v-if="!loading && !policies.length"
          type="info"
          variant="tonal"
        >
          No existen politicas activas visibles.
        </v-alert>

        <v-expansion-panels
          v-else
          variant="accordion"
        >
          <v-expansion-panel
            v-for="policy in policies"
            :key="policy.id"
          >
            <v-expansion-panel-title>
              <div class="d-flex flex-column">
                <span>{{ policy.policy_type }} · {{ policy.version_code }}</span>
                <span class="text-caption text-medium-emphasis">
                  Publicada: {{ formatDateTime(policy.published_at || policy.created_at) }}
                </span>
              </div>
            </v-expansion-panel-title>

            <v-expansion-panel-text>
              <div style="white-space: pre-line;">
                {{ policy.content_markdown }}
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-card-text>
    </v-card>
  </div>
</template>
