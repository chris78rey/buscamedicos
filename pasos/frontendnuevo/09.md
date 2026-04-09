Sí. Para el **superusuario** el paquete coherente que sale del repo es este:

1. **Dashboard admin**
2. **Privacidad administrativa completa**

   * logs de acceso
   * políticas
   * incidentes
3. **Moderación**

   * por ahora solo **pantalla base mínima**
4. **Pagos / settlements**

   * por ahora solo **pantalla base mínima**

El repo ya deja claro que la parte realmente cerrada para administración es **privacidad**, mientras que **moderación** y **settlements** todavía están planteados como placeholders base y no como flujo real completo. También deja indicado que este paquete se resuelve **en frontend Nuxt**, no inventando backend nuevo para esas pantallas.  

Se debe pasarle al programador esto y **solo esto**:

```text
REEMPLAZAR EXACTAMENTE ESTOS ARCHIVOS Y NO TOCAR NADA MÁS:

1. web_frontend/types/privacy.ts
2. web_frontend/composables/useApi.ts
3. web_frontend/pages/admin/dashboard.vue
4. web_frontend/pages/admin/privacy/access-logs.vue
5. web_frontend/pages/admin/privacy/policies.vue
6. web_frontend/pages/admin/privacy/incidents.vue
7. web_frontend/pages/admin/moderation/cases.vue
8. web_frontend/pages/admin/moderation/sanctions.vue
9. web_frontend/pages/admin/payments/settlements.vue

NO tocar backend.
NO crear endpoints nuevos.
NO refactorizar auth, layouts, middleware o store fuera de este alcance.
```

---

## 1) `web_frontend/types/privacy.ts`

```ts
export type ConsentCreatePayload = {
  consent_type: string
  source: string
  evidence_file_id?: string | null
  expires_at?: string | null
  notes?: string | null
}

export type ConsentResponse = {
  id: string
  patient_id: string
  consent_type: string
  status: string
  granted_at: string
  revoked_at?: string | null
  expires_at?: string | null
  source: string
  evidence_file_id?: string | null
  granted_by_user_id?: string | null
  notes?: string | null
}

export type PrivacyPolicyVersion = {
  id: string
  policy_type: string
  version_code: string
  content_markdown: string
  is_active: boolean
  published_at?: string | null
  created_at: string
}

export type PrivacyPolicyVersionCreatePayload = {
  policy_type: string
  version_code: string
  content_markdown: string
}

export type ClinicalAccessLog = {
  id: string
  actor_user_id: string
  actor_role_code: string
  patient_id?: string | null
  target_user_id?: string | null
  resource_type: string
  resource_id?: string | null
  access_mode: string
  action: string
  decision: string
  exceptional_access_request_id?: string | null
  justification?: string | null
  created_at: string
}

export type PrivacyAuditorAccessLogsResponse = {
  logs: ClinicalAccessLog[]
  count: number
}

export type ResourceAccessPolicy = {
  resource_type: string
  classification_code: string
  access_mode: string
  requires_relationship: boolean
  requires_patient_authorization: boolean
  requires_justification: boolean
  max_access_minutes?: number | null
  allow_download: boolean
  is_active: boolean
}

export type ResourceAccessPolicyUpdatePayload = {
  classification_code: string
  access_mode: string
  requires_relationship: boolean
  requires_patient_authorization: boolean
  requires_justification: boolean
  max_access_minutes?: number | null
  allow_download: boolean
}

export type RetentionPolicy = {
  id: string
  code: string
  resource_type: string
  retention_days?: number | null
  archive_after_days?: number | null
  delete_mode: string
  description?: string | null
  is_active: boolean
}

export type RetentionPolicyCreatePayload = {
  code: string
  resource_type: string
  retention_days?: number | null
  archive_after_days?: number | null
  delete_mode: string
  description?: string | null
}

export type PrivacyIncident = {
  id: string
  incident_code: string
  detected_at: string
  reported_by_user_id?: string | null
  severity: string
  incident_type: string
  description: string
  affected_resource_type?: string | null
  affected_resource_id?: string | null
  status: string
  assigned_admin_id?: string | null
  resolution_summary?: string | null
  resolved_at?: string | null
}

export type PrivacyIncidentCreatePayload = {
  incident_type: string
  severity: string
  description: string
  affected_resource_type?: string | null
  affected_resource_id?: string | null
}

export type PrivacyIncidentAssignPayload = {
  admin_id: string
}

export type PrivacyIncidentResolvePayload = {
  summary: string
}

export type PrivacyIncidentDismissPayload = {
  summary: string
}

export type ExceptionalAccessRequestCreatePayload = {
  patient_id?: string | null
  target_user_id?: string | null
  resource_type: string
  resource_id?: string | null
  scope_type: string
  justification: string
  business_basis?: string | null
  requested_minutes: number
}

export type ExceptionalAccessRequestResponse = {
  id: string
  requester_user_id: string
  requester_role_code: string
  patient_id?: string | null
  target_user_id?: string | null
  resource_type: string
  resource_id?: string | null
  scope_type: string
  justification: string
  business_basis?: string | null
  requested_minutes: number
  status: string
  requires_patient_authorization: boolean
  patient_consent_id?: string | null
  approved_by_user_id?: string | null
  approved_at?: string | null
  rejected_by_user_id?: string | null
  rejected_at?: string | null
  rejection_reason?: string | null
  starts_at?: string | null
  expires_at?: string | null
  revoked_by_user_id?: string | null
  revoked_at?: string | null
  revoke_reason?: string | null
  created_at: string
}
```

---

## 2) `web_frontend/composables/useApi.ts`

```ts
import type {
  AppointmentCreatePayload,
  AppointmentCreatedResponse,
  AppointmentSummary,
} from '~/types/appointment'
import type {
  ClinicalAccessLog,
  ConsentCreatePayload,
  ConsentResponse,
  ExceptionalAccessRequestCreatePayload,
  ExceptionalAccessRequestResponse,
  PrivacyAuditorAccessLogsResponse,
  PrivacyIncident,
  PrivacyIncidentAssignPayload,
  PrivacyIncidentCreatePayload,
  PrivacyIncidentDismissPayload,
  PrivacyIncidentResolvePayload,
  PrivacyPolicyVersion,
  PrivacyPolicyVersionCreatePayload,
  ResourceAccessPolicy,
  ResourceAccessPolicyUpdatePayload,
  RetentionPolicy,
  RetentionPolicyCreatePayload,
} from '~/types/privacy'
import type {
  ProfessionalSearchFilters,
  PublicProfessionalDetail,
  PublicProfessionalListItem,
  SlotItem,
} from '~/types/professional'

type ApiFetchOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  headers?: HeadersInit
  body?: unknown
}

type AuditorLogFilters = {
  actor_user_id?: string
  patient_id?: string
  resource_type?: string
  from_date?: string
  to_date?: string
  limit?: number
}

type AdminPrivacyLogFilters = {
  actor_user_id?: string
  resource_type?: string
  from_date?: string
  to_date?: string
}

type AdminIncidentFilters = {
  status_filter?: string
  severity?: string
}

function normalizeHeaders(headers?: HeadersInit): Record<string, string> {
  if (!headers) {
    return {}
  }

  const resolvedHeaders = new Headers(headers)
  return Object.fromEntries(resolvedHeaders.entries())
}

function cleanQuery(params: Record<string, unknown>) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => {
      if (value === null || value === undefined) {
        return false
      }

      if (typeof value === 'string') {
        return value.trim().length > 0
      }

      return true
    }),
  )
}

function buildQueryString(params: Record<string, unknown>) {
  const query = cleanQuery(params)
  return new URLSearchParams(
    Object.entries(query).reduce<Record<string, string>>((acc, [key, value]) => {
      acc[key] = String(value)
      return acc
    }, {}),
  ).toString()
}

export function useApi() {
  const config = useRuntimeConfig()
  const token = useCookie<string | null>('access_token')

  async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...normalizeHeaders(options.headers),
    }

    if (token.value) {
      headers.Authorization = `Bearer ${token.value}`
    }

    return await $fetch<T>(`${config.public.apiBase}${path}`, {
      method: options.method,
      headers,
      body: options.body,
    })
  }

  async function searchProfessionals(
    filters: ProfessionalSearchFilters = {},
  ): Promise<PublicProfessionalListItem[]> {
    const queryString = buildQueryString({
      city: filters.city,
      specialty: filters.specialty,
      modality: filters.modality,
      available_date: filters.available_date,
    })

    const path = queryString ? `/public/professionals?${queryString}` : '/public/professionals'
    return await apiFetch<PublicProfessionalListItem[]>(path, { method: 'GET' })
  }

  async function getPublicProfessional(identifier: string): Promise<PublicProfessionalDetail> {
    return await apiFetch<PublicProfessionalDetail>(
      `/public/professionals/${encodeURIComponent(identifier)}`,
      { method: 'GET' },
    )
  }

  async function getSlots(
    professionalId: string,
    date: string,
    modality: string,
  ): Promise<SlotItem[]> {
    const query = new URLSearchParams({
      date,
      modality,
    }).toString()

    return await apiFetch<SlotItem[]>(
      `/public/professionals/${encodeURIComponent(professionalId)}/slots?${query}`,
      { method: 'GET' },
    )
  }

  async function createAppointment(
    payload: AppointmentCreatePayload,
  ): Promise<AppointmentCreatedResponse> {
    return await apiFetch<AppointmentCreatedResponse>('/patient/appointments', {
      method: 'POST',
      body: payload,
    })
  }

  async function getMyAppointments(): Promise<AppointmentSummary[]> {
    return await apiFetch<AppointmentSummary[]>('/patient/appointments', {
      method: 'GET',
    })
  }

  async function getPatientConsents(): Promise<ConsentResponse[]> {
    return await apiFetch<ConsentResponse[]>('/patient/privacy/consents', {
      method: 'GET',
    })
  }

  async function createPatientConsent(payload: ConsentCreatePayload): Promise<ConsentResponse> {
    return await apiFetch<ConsentResponse>('/patient/privacy/consents', {
      method: 'POST',
      body: payload,
    })
  }

  async function revokePatientConsent(consentId: string): Promise<ConsentResponse> {
    return await apiFetch<ConsentResponse>(`/patient/privacy/consents/${encodeURIComponent(consentId)}/revoke`, {
      method: 'POST',
    })
  }

  async function getPatientPrivacyPolicies(): Promise<PrivacyPolicyVersion[]> {
    return await apiFetch<PrivacyPolicyVersion[]>('/patient/privacy/policies/active', {
      method: 'GET',
    })
  }

  async function getPatientAccessLogs(): Promise<ClinicalAccessLog[]> {
    return await apiFetch<ClinicalAccessLog[]>('/patient/privacy/access-log/me', {
      method: 'GET',
    })
  }

  async function createExceptionalAccessRequest(
    payload: ExceptionalAccessRequestCreatePayload,
  ): Promise<ExceptionalAccessRequestResponse> {
    return await apiFetch<ExceptionalAccessRequestResponse>('/professionals/me/privacy/exceptional-access-requests', {
      method: 'POST',
      body: payload,
    })
  }

  async function getProfessionalExceptionalAccessRequests(): Promise<ExceptionalAccessRequestResponse[]> {
    return await apiFetch<ExceptionalAccessRequestResponse[]>('/professionals/me/privacy/exceptional-access-requests', {
      method: 'GET',
    })
  }

  async function getProfessionalAccessLogs(): Promise<ClinicalAccessLog[]> {
    return await apiFetch<ClinicalAccessLog[]>('/professionals/me/privacy/access-log/me', {
      method: 'GET',
    })
  }

  async function getPrivacyAuditorAccessLogs(
    filters: AuditorLogFilters = {},
  ): Promise<PrivacyAuditorAccessLogsResponse> {
    const queryString = buildQueryString({
      actor_user_id: filters.actor_user_id,
      patient_id: filters.patient_id,
      resource_type: filters.resource_type,
      from_date: filters.from_date,
      to_date: filters.to_date,
      limit: filters.limit,
    })

    const path = queryString ? `/privacy-auditor/access-logs?${queryString}` : '/privacy-auditor/access-logs'
    return await apiFetch<PrivacyAuditorAccessLogsResponse>(path, {
      method: 'GET',
    })
  }

  async function getAdminPrivacyPolicies(policyType?: string): Promise<PrivacyPolicyVersion[]> {
    const queryString = buildQueryString({
      policy_type: policyType,
    })

    const path = queryString ? `/admin/privacy/policies?${queryString}` : '/admin/privacy/policies'
    return await apiFetch<PrivacyPolicyVersion[]>(path, {
      method: 'GET',
    })
  }

  async function createAdminPrivacyPolicy(
    payload: PrivacyPolicyVersionCreatePayload,
  ): Promise<PrivacyPolicyVersion> {
    return await apiFetch<PrivacyPolicyVersion>('/admin/privacy/policies', {
      method: 'POST',
      body: payload,
    })
  }

  async function publishAdminPrivacyPolicy(policyId: string): Promise<PrivacyPolicyVersion> {
    return await apiFetch<PrivacyPolicyVersion>(`/admin/privacy/policies/${encodeURIComponent(policyId)}/publish`, {
      method: 'POST',
    })
  }

  async function getAdminPrivacyResourcePolicies(): Promise<ResourceAccessPolicy[]> {
    return await apiFetch<ResourceAccessPolicy[]>('/admin/privacy/resource-policies', {
      method: 'GET',
    })
  }

  async function updateAdminPrivacyResourcePolicy(
    resourceType: string,
    payload: ResourceAccessPolicyUpdatePayload,
  ): Promise<ResourceAccessPolicy> {
    return await apiFetch<ResourceAccessPolicy>(`/admin/privacy/resource-policies/${encodeURIComponent(resourceType)}`, {
      method: 'PUT',
      body: payload,
    })
  }

  async function getAdminPrivacyAccessLogs(
    filters: AdminPrivacyLogFilters = {},
  ): Promise<ClinicalAccessLog[]> {
    const queryString = buildQueryString({
      actor_user_id: filters.actor_user_id,
      resource_type: filters.resource_type,
      from_date: filters.from_date,
      to_date: filters.to_date,
    })

    const path = queryString ? `/admin/privacy/access-logs?${queryString}` : '/admin/privacy/access-logs'
    return await apiFetch<ClinicalAccessLog[]>(path, {
      method: 'GET',
    })
  }

  async function exportAdminPrivacyAccessLogsMeta(
    filters: AdminPrivacyLogFilters = {},
  ): Promise<ClinicalAccessLog[]> {
    const queryString = buildQueryString({
      actor_user_id: filters.actor_user_id,
      resource_type: filters.resource_type,
      from_date: filters.from_date,
      to_date: filters.to_date,
    })

    const path = queryString
      ? `/admin/privacy/access-logs/export-meta?${queryString}`
      : '/admin/privacy/access-logs/export-meta'

    return await apiFetch<ClinicalAccessLog[]>(path, {
      method: 'GET',
    })
  }

  async function getAdminPrivacyRetentionPolicies(): Promise<RetentionPolicy[]> {
    return await apiFetch<RetentionPolicy[]>('/admin/privacy/retention-policies', {
      method: 'GET',
    })
  }

  async function createAdminPrivacyRetentionPolicy(
    payload: RetentionPolicyCreatePayload,
  ): Promise<RetentionPolicy> {
    return await apiFetch<RetentionPolicy>('/admin/privacy/retention-policies', {
      method: 'POST',
      body: payload,
    })
  }

  async function updateAdminPrivacyRetentionPolicy(
    policyId: string,
    payload: RetentionPolicyCreatePayload,
  ): Promise<RetentionPolicy> {
    return await apiFetch<RetentionPolicy>(`/admin/privacy/retention-policies/${encodeURIComponent(policyId)}`, {
      method: 'PUT',
      body: payload,
    })
  }

  async function getAdminPrivacyIncidents(
    filters: AdminIncidentFilters = {},
  ): Promise<PrivacyIncident[]> {
    const queryString = buildQueryString({
      status_filter: filters.status_filter,
      severity: filters.severity,
    })

    const path = queryString ? `/admin/privacy/incidents?${queryString}` : '/admin/privacy/incidents'
    return await apiFetch<PrivacyIncident[]>(path, {
      method: 'GET',
    })
  }

  async function createAdminPrivacyIncident(
    payload: PrivacyIncidentCreatePayload,
  ): Promise<PrivacyIncident> {
    return await apiFetch<PrivacyIncident>('/admin/privacy/incidents', {
      method: 'POST',
      body: payload,
    })
  }

  async function assignAdminPrivacyIncident(
    incidentId: string,
    payload: PrivacyIncidentAssignPayload,
  ): Promise<PrivacyIncident> {
    return await apiFetch<PrivacyIncident>(`/admin/privacy/incidents/${encodeURIComponent(incidentId)}/assign`, {
      method: 'POST',
      body: payload,
    })
  }

  async function containAdminPrivacyIncident(
    incidentId: string,
  ): Promise<PrivacyIncident> {
    return await apiFetch<PrivacyIncident>(`/admin/privacy/incidents/${encodeURIComponent(incidentId)}/contain`, {
      method: 'POST',
    })
  }

  async function resolveAdminPrivacyIncident(
    incidentId: string,
    payload: PrivacyIncidentResolvePayload,
  ): Promise<PrivacyIncident> {
    return await apiFetch<PrivacyIncident>(`/admin/privacy/incidents/${encodeURIComponent(incidentId)}/resolve`, {
      method: 'POST',
      body: payload,
    })
  }

  async function dismissAdminPrivacyIncident(
    incidentId: string,
    payload: PrivacyIncidentDismissPayload,
  ): Promise<PrivacyIncident> {
    return await apiFetch<PrivacyIncident>(`/admin/privacy/incidents/${encodeURIComponent(incidentId)}/dismiss`, {
      method: 'POST',
      body: payload,
    })
  }

  return {
    apiFetch,
    searchProfessionals,
    getPublicProfessional,
    getSlots,
    createAppointment,
    getMyAppointments,
    getPatientConsents,
    createPatientConsent,
    revokePatientConsent,
    getPatientPrivacyPolicies,
    getPatientAccessLogs,
    createExceptionalAccessRequest,
    getProfessionalExceptionalAccessRequests,
    getProfessionalAccessLogs,
    getPrivacyAuditorAccessLogs,
    getAdminPrivacyPolicies,
    createAdminPrivacyPolicy,
    publishAdminPrivacyPolicy,
    getAdminPrivacyResourcePolicies,
    updateAdminPrivacyResourcePolicy,
    getAdminPrivacyAccessLogs,
    exportAdminPrivacyAccessLogsMeta,
    getAdminPrivacyRetentionPolicies,
    createAdminPrivacyRetentionPolicy,
    updateAdminPrivacyRetentionPolicy,
    getAdminPrivacyIncidents,
    createAdminPrivacyIncident,
    assignAdminPrivacyIncident,
    containAdminPrivacyIncident,
    resolveAdminPrivacyIncident,
    dismissAdminPrivacyIncident,
  }
}
```

---

## 3) `web_frontend/pages/admin/dashboard.vue`

```vue
<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_validation', 'admin_support', 'admin_moderation', 'admin_privacy'],
})

const cards = [
  {
    title: 'Privacidad',
    text: 'Accede a logs, politicas e incidentes regulatorios.',
    to: '/admin/privacy/access-logs',
    icon: 'mdi-shield-search',
  },
  {
    title: 'Moderacion',
    text: 'Supervisa casos y sanciones en el ecosistema.',
    to: '/admin/moderation/cases',
    icon: 'mdi-gavel',
  },
  {
    title: 'Pagos',
    text: 'Revisa settlements y operaciones del marketplace.',
    to: '/admin/payments/settlements',
    icon: 'mdi-cash-multiple',
  },
]
</script>

<template>
  <v-row>
    <v-col v-for="card in cards" :key="card.to" cols="12" md="4">
      <v-card class="h-100" rounded="xl">
        <v-card-item :prepend-icon="card.icon">
          <v-card-title>{{ card.title }}</v-card-title>
        </v-card-item>
        <v-card-text>{{ card.text }}</v-card-text>
        <v-card-actions>
          <v-btn :to="card.to" color="primary" variant="tonal">
            Abrir
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-col>
  </v-row>
</template>
```

---

## 4) `web_frontend/pages/admin/privacy/access-logs.vue`

```vue
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
```

---

## 5) `web_frontend/pages/admin/privacy/policies.vue`

```vue
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
```

---

## 6) `web_frontend/pages/admin/privacy/incidents.vue`

```vue
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
      max-width="520"
    >
      <v-card rounded="xl">
        <v-card-item>
          <v-card-title>
            {{
              actionType === 'assign'
                ? 'Asignar incidente'
                : actionType === 'contain'
                  ? 'Contener incidente'
                  : actionType === 'resolve'
                    ? 'Resolver incidente'
                    : 'Descartar incidente'
            }}
          </v-card-title>
        </v-card-item>

        <v-card-text>
          <div class="mb-4 text-body-2">
            {{ selectedIncident?.incident_code }}
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
            :label="actionType === 'resolve' ? 'Resumen de resolucion' : 'Resumen de descarte'"
            prepend-inner-icon="mdi-text-box-outline"
            rows="2"
            variant="outlined"
          />

          <v-alert
            v-if="actionType === 'contain'"
            type="info"
            variant="tonal"
          >
            La accion de contencion usa el endpoint directo sin campos adicionales.
          </v-alert>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
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
```

---

## 7) `web_frontend/pages/admin/moderation/cases.vue`

```vue
<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_validation', 'admin_support', 'admin_moderation', 'admin_privacy'],
})
</script>

<template>
  <v-card rounded="xl">
    <v-card-item>
      <v-card-title>Casos de moderación</v-card-title>
      <v-card-subtitle>
        Pantalla base para futura conexión de cola de denuncias y revisión.
      </v-card-subtitle>
    </v-card-item>
    <v-card-text>
      Se debe conectar a endpoints reales de denuncias, revisión, decisión y bitácora cuando esa fase sea implementada.
    </v-card-text>
  </v-card>
</template>
```

---

## 8) `web_frontend/pages/admin/moderation/sanctions.vue`

```vue
<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_validation', 'admin_support', 'admin_moderation', 'admin_privacy'],
})
</script>

<template>
  <v-card rounded="xl">
    <v-card-item>
      <v-card-title>Sanciones</v-card-title>
      <v-card-subtitle>
        Pantalla base para gestión de sanciones futuras.
      </v-card-subtitle>
    </v-card-item>
    <v-card-text>
      Se debe conectar a endpoints de suspensión, restricción, levantamiento y auditoría cuando exista la fase de moderación.
    </v-card-text>
  </v-card>
</template>
```

---

## 9) `web_frontend/pages/admin/payments/settlements.vue`

```vue
<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_validation', 'admin_support', 'admin_moderation', 'admin_privacy'],
})
</script>

<template>
  <v-card rounded="xl">
    <v-card-item>
      <v-card-title>Settlements</v-card-title>
      <v-card-subtitle>
        Pantalla base para fase financiera administrativa.
      </v-card-subtitle>
    </v-card-item>
    <v-card-text>
      Se debe conectar a endpoints reales de liquidaciones, conciliación, estado y exportación cuando la fase financiera quede cerrada.
    </v-card-text>
  </v-card>
</template>
```

---

## Comando de prueba

```bash
cd web_frontend
npm install
NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1 npm run dev
```

Ese es el paquete correcto para que el superusuario quede operativo **hasta donde el repo ya lo soporta hoy**: dashboard admin, privacidad administrativa completa, y placeholders controlados para moderación y settlements. El material consolidado del repo muestra exactamente esa frontera funcional.   

Archivo revisado: [repomix_buscamedicos_full_ai.xml](sandbox:/mnt/data/repomix_buscamedicos_full_ai.xml)
