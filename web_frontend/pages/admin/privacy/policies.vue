<script setup lang="ts">
import { FetchError } from 'ofetch'

import type {
  PrivacyPolicyVersion,
  PrivacyPolicyVersionCreatePayload,
  ResourceAccessPolicy,
  ResourceAccessPolicyUpdatePayload,
  RetentionPolicy,
  RetentionPolicyCreatePayload,
} from '~/types/privacy'

definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_validation', 'admin_support', 'admin_moderation', 'admin_privacy'],
})

const {
  getAdminPrivacyPolicies,
  createAdminPrivacyPolicy,
  publishAdminPrivacyPolicy,
  getAdminPrivacyResourcePolicies,
  updateAdminPrivacyResourcePolicy,
  getAdminPrivacyRetentionPolicies,
  createAdminPrivacyRetentionPolicy,
  updateAdminPrivacyRetentionPolicy,
} = useApi()

const loading = ref(false)
const submittingPolicy = ref(false)
const submittingResourcePolicy = ref(false)
const submittingRetentionPolicy = ref(false)
const publishingPolicyId = ref<string | null>(null)
const editingRetentionPolicyId = ref<string | null>(null)
const errorMessage = ref('')
const successMessage = ref('')

const policies = ref<PrivacyPolicyVersion[]>([])
const resourcePolicies = ref<ResourceAccessPolicy[]>([])
const retentionPolicies = ref<RetentionPolicy[]>([])

const policyForm = reactive<PrivacyPolicyVersionCreatePayload>({
  policy_type: 'privacy_notice',
  version_code: '',
  content_markdown: '',
})

const resourcePolicyForm = reactive<ResourceAccessPolicyUpdatePayload & { resource_type: string }>({
  resource_type: '',
  classification_code: 'clinical_restricted',
  access_mode: 'contextual',
  requires_relationship: true,
  requires_patient_authorization: false,
  requires_justification: false,
  max_access_minutes: 30,
  allow_download: false,
})

const retentionForm = reactive<RetentionPolicyCreatePayload>({
  code: '',
  resource_type: '',
  retention_days: 365,
  archive_after_days: 180,
  delete_mode: 'soft_delete',
  description: '',
})

const accessModeOptions = ['contextual', 'strict', 'metadata_only']
const policyTypeOptions = ['privacy_notice', 'teleconsultation_terms', 'data_processing', 'exceptional_access']
const deleteModeOptions = ['soft_delete', 'archive_only', 'manual_review']

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

async function loadData() {
  loading.value = true
  resetMessages()

  try {
    const [policyList, resourcePolicyList, retentionList] = await Promise.all([
      getAdminPrivacyPolicies(),
      getAdminPrivacyResourcePolicies(),
      getAdminPrivacyRetentionPolicies(),
    ])

    policies.value = policyList
    resourcePolicies.value = resourcePolicyList
    retentionPolicies.value = retentionList
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo cargar la configuracion de privacidad.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado cargando privacidad.'
    }
  }
  finally {
    loading.value = false
  }
}

async function handleCreatePolicy() {
  submittingPolicy.value = true
  resetMessages()

  try {
    await createAdminPrivacyPolicy({
      policy_type: policyForm.policy_type.trim(),
      version_code: policyForm.version_code.trim(),
      content_markdown: policyForm.content_markdown.trim(),
    })

    successMessage.value = 'Politica creada correctamente.'
    policyForm.version_code = ''
    policyForm.content_markdown = ''
    await loadData()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo crear la politica.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado creando la politica.'
    }
  }
  finally {
    submittingPolicy.value = false
  }
}

async function handlePublishPolicy(policyId: string) {
  publishingPolicyId.value = policyId
  resetMessages()

  try {
    await publishAdminPrivacyPolicy(policyId)
    successMessage.value = 'Politica publicada correctamente.'
    await loadData()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo publicar la politica.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado publicando la politica.'
    }
  }
  finally {
    publishingPolicyId.value = null
  }
}

async function handleSaveResourcePolicy() {
  submittingResourcePolicy.value = true
  resetMessages()

  try {
    await updateAdminPrivacyResourcePolicy(resourcePolicyForm.resource_type.trim(), {
      classification_code: resourcePolicyForm.classification_code.trim(),
      access_mode: resourcePolicyForm.access_mode.trim(),
      requires_relationship: Boolean(resourcePolicyForm.requires_relationship),
      requires_patient_authorization: Boolean(resourcePolicyForm.requires_patient_authorization),
      requires_justification: Boolean(resourcePolicyForm.requires_justification),
      max_access_minutes: resourcePolicyForm.max_access_minutes || null,
      allow_download: Boolean(resourcePolicyForm.allow_download),
    })

    successMessage.value = 'Policy de recurso actualizada correctamente.'
    await loadData()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo actualizar la policy de recurso.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado actualizando la policy de recurso.'
    }
  }
  finally {
    submittingResourcePolicy.value = false
  }
}

function fillResourcePolicyForm(item: ResourceAccessPolicy) {
  resourcePolicyForm.resource_type = item.resource_type
  resourcePolicyForm.classification_code = item.classification_code
  resourcePolicyForm.access_mode = item.access_mode
  resourcePolicyForm.requires_relationship = item.requires_relationship
  resourcePolicyForm.requires_patient_authorization = item.requires_patient_authorization
  resourcePolicyForm.requires_justification = item.requires_justification
  resourcePolicyForm.max_access_minutes = item.max_access_minutes ?? 30
  resourcePolicyForm.allow_download = item.allow_download
}

async function handleSaveRetentionPolicy() {
  submittingRetentionPolicy.value = true
  resetMessages()

  try {
    const payload: RetentionPolicyCreatePayload = {
      code: retentionForm.code.trim(),
      resource_type: retentionForm.resource_type.trim(),
      retention_days: retentionForm.retention_days || null,
      archive_after_days: retentionForm.archive_after_days || null,
      delete_mode: retentionForm.delete_mode.trim(),
      description: retentionForm.description?.trim() || null,
    }

    if (editingRetentionPolicyId.value) {
      await updateAdminPrivacyRetentionPolicy(editingRetentionPolicyId.value, payload)
      successMessage.value = 'Retention policy actualizada correctamente.'
    }
    else {
      await createAdminPrivacyRetentionPolicy(payload)
      successMessage.value = 'Retention policy creada correctamente.'
    }

    editingRetentionPolicyId.value = null
    retentionForm.code = ''
    retentionForm.resource_type = ''
    retentionForm.retention_days = 365
    retentionForm.archive_after_days = 180
    retentionForm.delete_mode = 'soft_delete'
    retentionForm.description = ''
    await loadData()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo guardar la retention policy.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado guardando la retention policy.'
    }
  }
  finally {
    submittingRetentionPolicy.value = false
  }
}

function editRetentionPolicy(item: RetentionPolicy) {
  editingRetentionPolicyId.value = item.id
  retentionForm.code = item.code
  retentionForm.resource_type = item.resource_type
  retentionForm.retention_days = item.retention_days ?? null
  retentionForm.archive_after_days = item.archive_after_days ?? null
  retentionForm.delete_mode = item.delete_mode
  retentionForm.description = item.description ?? ''
}

function resetRetentionForm() {
  editingRetentionPolicyId.value = null
  retentionForm.code = ''
  retentionForm.resource_type = ''
  retentionForm.retention_days = 365
  retentionForm.archive_after_days = 180
  retentionForm.delete_mode = 'soft_delete'
  retentionForm.description = ''
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <div class="d-flex justify-space-between align-center flex-wrap ga-3">
      <div>
        <h2 class="text-h5">Politicas</h2>
        <p class="text-body-2 text-medium-emphasis mb-0">
          Gestion basica de versiones de politica, reglas por recurso y retention policies.
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
        <v-card-title>Nueva version de politica</v-card-title>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-select
              v-model="policyForm.policy_type"
              :items="policyTypeOptions"
              label="Policy type"
              prepend-inner-icon="mdi-shield-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-text-field
              v-model="policyForm.version_code"
              label="Version code"
              prepend-inner-icon="mdi-tag-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="6">
            <v-textarea
              v-model="policyForm.content_markdown"
              auto-grow
              label="Contenido markdown"
              prepend-inner-icon="mdi-text-box-outline"
              rows="2"
              variant="outlined"
            />
          </v-col>
        </v-row>

        <div class="d-flex justify-end">
          <v-btn
            :loading="submittingPolicy"
            color="primary"
            prepend-icon="mdi-content-save-outline"
            @click="handleCreatePolicy"
          >
            Crear politica
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <v-card rounded="xl">
      <v-card-item>
        <v-card-title>Versiones disponibles</v-card-title>
      </v-card-item>

      <v-card-text>
        <v-alert
          v-if="!loading && !policies.length"
          type="info"
          variant="tonal"
        >
          No existen politicas cargadas.
        </v-alert>

        <v-row v-else>
          <v-col
            v-for="policy in policies"
            :key="policy.id"
            cols="12"
            md="6"
          >
            <v-card class="h-100" rounded="xl" variant="tonal">
              <v-card-item>
                <template #append>
                  <v-chip
                    :color="policy.is_active ? 'success' : 'grey'"
                    variant="tonal"
                  >
                    {{ policy.is_active ? 'Activa' : 'Borrador' }}
                  </v-chip>
                </template>

                <v-card-title>{{ policy.policy_type }}</v-card-title>
                <v-card-subtitle>{{ policy.version_code }}</v-card-subtitle>
              </v-card-item>

              <v-card-text class="d-flex flex-column ga-2">
                <div>
                  <div class="text-caption text-medium-emphasis">Creada</div>
                  <div class="text-body-2">{{ formatDateTime(policy.created_at) }}</div>
                </div>

                <div>
                  <div class="text-caption text-medium-emphasis">Publicada</div>
                  <div class="text-body-2">{{ formatDateTime(policy.published_at) }}</div>
                </div>

                <div style="white-space: pre-line;">
                  {{ policy.content_markdown }}
                </div>
              </v-card-text>

              <v-card-actions>
                <v-btn
                  :disabled="policy.is_active"
                  :loading="publishingPolicyId === policy.id"
                  color="primary"
                  prepend-icon="mdi-publish"
                  variant="tonal"
                  @click="handlePublishPolicy(policy.id)"
                >
                  Publicar
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card rounded="xl">
      <v-card-item>
        <v-card-title>Policy por recurso</v-card-title>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="resourcePolicyForm.resource_type"
              label="Resource type"
              prepend-inner-icon="mdi-file-cog-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-text-field
              v-model="resourcePolicyForm.classification_code"
              label="Classification code"
              prepend-inner-icon="mdi-shield-lock-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-select
              v-model="resourcePolicyForm.access_mode"
              :items="accessModeOptions"
              label="Access mode"
              prepend-inner-icon="mdi-tune-variant"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-text-field
              v-model.number="resourcePolicyForm.max_access_minutes"
              label="Max access minutes"
              min="0"
              type="number"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-switch
              v-model="resourcePolicyForm.requires_relationship"
              color="primary"
              label="Requires relationship"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-switch
              v-model="resourcePolicyForm.requires_patient_authorization"
              color="primary"
              label="Requires patient authorization"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-switch
              v-model="resourcePolicyForm.requires_justification"
              color="primary"
              label="Requires justification"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-switch
              v-model="resourcePolicyForm.allow_download"
              color="primary"
              label="Allow download"
            />
          </v-col>
        </v-row>

        <div class="d-flex justify-end">
          <v-btn
            :loading="submittingResourcePolicy"
            color="primary"
            prepend-icon="mdi-content-save-outline"
            @click="handleSaveResourcePolicy"
          >
            Guardar policy
          </v-btn>
        </div>

        <v-divider class="my-6" />

        <v-row>
          <v-col
            v-for="item in resourcePolicies"
            :key="item.resource_type"
            cols="12"
            md="6"
          >
            <v-card rounded="xl" variant="tonal">
              <v-card-item>
                <template #append>
                  <v-chip
                    :color="item.is_active ? 'success' : 'grey'"
                    variant="tonal"
                  >
                    {{ item.is_active ? 'Activa' : 'Inactiva' }}
                  </v-chip>
                </template>

                <v-card-title>{{ item.resource_type }}</v-card-title>
                <v-card-subtitle>{{ item.classification_code }}</v-card-subtitle>
              </v-card-item>

              <v-card-text class="d-flex flex-column ga-2">
                <div>Modo: {{ item.access_mode }}</div>
                <div>Relacion: {{ item.requires_relationship ? 'Si' : 'No' }}</div>
                <div>Autorizacion paciente: {{ item.requires_patient_authorization ? 'Si' : 'No' }}</div>
                <div>Justificacion: {{ item.requires_justification ? 'Si' : 'No' }}</div>
                <div>Descarga: {{ item.allow_download ? 'Si' : 'No' }}</div>
                <div>Minutos maximos: {{ item.max_access_minutes ?? 'No definido' }}</div>
              </v-card-text>

              <v-card-actions>
                <v-btn
                  color="primary"
                  prepend-icon="mdi-pencil"
                  variant="tonal"
                  @click="fillResourcePolicyForm(item)"
                >
                  Cargar en formulario
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card rounded="xl">
      <v-card-item>
        <v-card-title>Retention policies</v-card-title>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="retentionForm.code"
              label="Code"
              prepend-inner-icon="mdi-tag-multiple-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-text-field
              v-model="retentionForm.resource_type"
              label="Resource type"
              prepend-inner-icon="mdi-database-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="2">
            <v-text-field
              v-model.number="retentionForm.retention_days"
              label="Retention days"
              min="0"
              type="number"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="2">
            <v-text-field
              v-model.number="retentionForm.archive_after_days"
              label="Archive after days"
              min="0"
              type="number"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="2">
            <v-select
              v-model="retentionForm.delete_mode"
              :items="deleteModeOptions"
              label="Delete mode"
              prepend-inner-icon="mdi-delete-clock-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12">
            <v-textarea
              v-model="retentionForm.description"
              auto-grow
              label="Descripcion"
              prepend-inner-icon="mdi-note-text-outline"
              rows="1"
              variant="outlined"
            />
          </v-col>
        </v-row>

        <div class="d-flex flex-wrap justify-end ga-3">
          <v-btn
            v-if="editingRetentionPolicyId"
            prepend-icon="mdi-close"
            variant="outlined"
            @click="resetRetentionForm"
          >
            Cancelar edicion
          </v-btn>

          <v-btn
            :loading="submittingRetentionPolicy"
            color="primary"
            prepend-icon="mdi-content-save-outline"
            @click="handleSaveRetentionPolicy"
          >
            {{ editingRetentionPolicyId ? 'Actualizar retention' : 'Crear retention' }}
          </v-btn>
        </div>

        <v-divider class="my-6" />

        <v-row>
          <v-col
            v-for="item in retentionPolicies"
            :key="item.id"
            cols="12"
            md="6"
          >
            <v-card rounded="xl" variant="tonal">
              <v-card-item>
                <template #append>
                  <v-chip
                    :color="item.is_active ? 'success' : 'grey'"
                    variant="tonal"
                  >
                    {{ item.is_active ? 'Activa' : 'Inactiva' }}
                  </v-chip>
                </template>

                <v-card-title>{{ item.code }}</v-card-title>
                <v-card-subtitle>{{ item.resource_type }}</v-card-subtitle>
              </v-card-item>

              <v-card-text class="d-flex flex-column ga-2">
                <div>Retention: {{ item.retention_days ?? 'No definido' }}</div>
                <div>Archive after: {{ item.archive_after_days ?? 'No definido' }}</div>
                <div>Delete mode: {{ item.delete_mode }}</div>
                <div>{{ item.description || 'Sin descripcion' }}</div>
              </v-card-text>

              <v-card-actions>
                <v-btn
                  color="primary"
                  prepend-icon="mdi-pencil"
                  variant="tonal"
                  @click="editRetentionPolicy(item)"
                >
                  Editar
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>
