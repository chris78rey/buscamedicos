<script setup lang="ts">
import type { AdminVerificationRequestDetail, AdminDocumentResponse } from '~/types/verification'

definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_validation', 'admin_support'],
})

const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()
const { apiFetch } = useApi()


const requestId = route.params.id as string

const detail = ref<AdminVerificationRequestDetail | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(() => {
  console.log('Runtime Config:', config.public)
  console.log('API Base:', config.public.apiBase)
})

const actionLoading = ref(false)
const actionError = ref<string | null>(null)
const actionSuccess = ref<string | null>(null)

const rejectDialog = ref(false)
const rejectReason = ref('')
const correctionDialog = ref(false)
const correctionReason = ref('')
const approveNotesDialog = ref(false)
const approveNotes = ref('')

const documentTypeLabels: Record<string, string> = {
  national_id_front: 'Cédula (Frente)',
  national_id_back: 'Cédula (Reverso)',
  degree: 'Título Profesional',
  registration_certificate: 'Certificado de Registro',
  selfie_verification: 'Selfie con Cédula',
  cv: 'Currículum Vitae',
  signed_agreement: 'Acuerdo Firmado',
  supporting_document: 'Documento de Respaldo',
}

const reviewStatusColors: Record<string, string> = {
  pending: 'warning',
  approved: 'success',
  rejected: 'error',
}

async function loadDetail() {
  loading.value = true
  error.value = null
  try {
    detail.value = await apiFetch<AdminVerificationRequestDetail>(
      `/admin/verification-requests/${encodeURIComponent(requestId)}`,
      { method: 'GET' },
    )
  }
  catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error al cargar detalle'
  }
  finally {
    loading.value = false
  }
}

async function assignRequest() {
  actionLoading.value = true
  actionError.value = null
  actionSuccess.value = null
  try {
    await apiFetch(`/admin/verification-requests/${encodeURIComponent(requestId)}/assign`, { method: 'POST' })
    actionSuccess.value = 'Solicitud asignada'
    await loadDetail()
  }
  catch (e: unknown) {
    actionError.value = e instanceof Error ? e.message : 'Error al asignar'
  }
  finally {
    actionLoading.value = false
  }
}

async function approveDocument(doc: AdminDocumentResponse) {
  actionLoading.value = true
  actionError.value = null
  actionSuccess.value = null
  try {
    await apiFetch(
      `/admin/verification-requests/${encodeURIComponent(requestId)}/documents/${encodeURIComponent(doc.id)}/approve`,
      { method: 'POST', body: {} },
    )
    actionSuccess.value = `Documento "${documentTypeLabels[doc.document_type] ?? doc.document_type}" aprobado`
    await loadDetail()
  }
  catch (e: unknown) {
    actionError.value = e instanceof Error ? e.message : 'Error al aprobar documento'
  }
  finally {
    actionLoading.value = false
  }
}

async function rejectDocument(doc: AdminDocumentResponse) {
  if (!rejectReason.value.trim()) {
    actionError.value = 'Debe ingresar un motivo de rechazo'
    return
  }
  actionLoading.value = true
  actionError.value = null
  actionSuccess.value = null
  try {
    await apiFetch(
      `/admin/verification-requests/${encodeURIComponent(requestId)}/documents/${encodeURIComponent(doc.id)}/reject`,
      { method: 'POST', body: { reason: rejectReason.value } },
    )
    actionSuccess.value = `Documento "${documentTypeLabels[doc.document_type] ?? doc.document_type}" rechazado`
    rejectDialog.value = false
    rejectReason.value = ''
    await loadDetail()
  }
  catch (e: unknown) {
    actionError.value = e instanceof Error ? e.message : 'Error al rechazar documento'
  }
  finally {
    actionLoading.value = false
  }
}

async function approveRequest() {
  actionLoading.value = true
  actionError.value = null
  actionSuccess.value = null
  try {
    await apiFetch(
      `/admin/verification-requests/${encodeURIComponent(requestId)}/approve`,
      { method: 'POST' },
    )
    actionSuccess.value = 'Solicitud aprobada. Profesional activado.'
    await loadDetail()
  }
  catch (e: unknown) {
    actionError.value = e instanceof Error ? e.message : 'Error al aprobar solicitud'
  }
  finally {
    actionLoading.value = false
  }
}

async function rejectRequest() {
  if (!rejectReason.value.trim()) {
    actionError.value = 'Debe ingresar un motivo de rechazo'
    return
  }
  actionLoading.value = true
  actionError.value = null
  actionSuccess.value = null
  try {
    await apiFetch(
      `/admin/verification-requests/${encodeURIComponent(requestId)}/reject`,
      { method: 'POST', body: { reason: rejectReason.value } },
    )
    actionSuccess.value = 'Solicitud rechazada'
    rejectDialog.value = false
    rejectReason.value = ''
    await loadDetail()
  }
  catch (e: unknown) {
    actionError.value = e instanceof Error ? e.message : 'Error al rechazar solicitud'
  }
  finally {
    actionLoading.value = false
  }
}

async function requestCorrection() {
  if (!correctionReason.value.trim()) {
    actionError.value = 'Debe ingresar el motivo de corrección'
    return
  }
  actionLoading.value = true
  actionError.value = null
  actionSuccess.value = null
  try {
    await apiFetch(
      `/admin/verification-requests/${encodeURIComponent(requestId)}/request-correction`,
      { method: 'POST', body: { reason: correctionReason.value } },
    )
    actionSuccess.value = 'Corrección solicitada al profesional'
    correctionDialog.value = false
    correctionReason.value = ''
    await loadDetail()
  }
  catch (e: unknown) {
    actionError.value = e instanceof Error ? e.message : 'Error al solicitar corrección'
  }
  finally {
    actionLoading.value = false
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

const canApprove = computed(() => {
  if (!detail.value) return false
  return detail.value.documents.some(
    d => d.document_type === 'degree' && d.review_status === 'approved',
  )
})

onMounted(() => {
  loadDetail()
})
</script>

<template>
  <div>
    <v-btn class="mb-4" variant="text" :to="'/admin/verification'">
      <v-icon start>mdi-arrow-left</v-icon>
      Volver a solicitudes
    </v-btn>

    <v-alert v-if="actionError" type="error" class="mb-4" closable @click:close="actionError = null">
      {{ actionError }}
    </v-alert>
    <v-alert v-if="actionSuccess" type="success" class="mb-4" closable @click:close="actionSuccess = null">
      {{ actionSuccess }}
    </v-alert>

    <v-card v-if="loading" class="text-center pa-8">
      <v-progress-circular indeterminate color="primary" />
      <p class="mt-4">Cargando...</p>
    </v-card>

    <div v-else-if="detail">
      <v-row>
        <v-col cols="12" lg="4">
          <v-card rounded="xl" class="mb-4">
            <v-card-item>
              <v-card-title>Profesional</v-card-title>
            </v-card-item>
            <v-card-text>
              <p class="text-h6">{{ detail.professional?.public_display_name }}</p>
              <p class="text-body-2 text-medium-emphasis">{{ detail.professional?.email }}</p>
              <p class="text-body-2">
                <strong>Tipo:</strong> {{ detail.professional?.professional_type }}
              </p>
            </v-card-text>
          </v-card>

          <v-card v-if="detail.person" rounded="xl" class="mb-4">
            <v-card-item>
              <v-card-title>Datos Personales</v-card-title>
            </v-card-item>
            <v-card-text>
              <p><strong>Nombre:</strong> {{ detail.person.first_name }} {{ detail.person.last_name }}</p>
              <p><strong>Cédula:</strong> {{ detail.person.national_id }}</p>
              <p><strong>Teléfono:</strong> {{ detail.person.phone }}</p>
            </v-card-text>
          </v-card>

          <v-card rounded="xl" class="mb-4">
            <v-card-item>
              <v-card-title>Estado de la Solicitud</v-card-title>
            </v-card-item>
            <v-card-text>
              <v-chip
                :color="
                  detail.status === 'approved' ? 'success'
                    : detail.status === 'rejected' ? 'error'
                    : detail.status === 'under_review' ? 'warning'
                    : 'info'
                "
                class="mb-3"
              >
                {{ detail.status.replace('_', ' ') }}
              </v-chip>
              <p class="text-body-2">
                <strong>Enviada:</strong> {{ formatDate(detail.submitted_at) }}
              </p>
              <p v-if="detail.assigned_admin_id" class="text-body-2">
                <strong>Asignada a:</strong> {{ detail.assigned_admin_id }}
              </p>
              <p v-if="detail.decision_at" class="text-body-2">
                <strong>Decisión:</strong> {{ formatDate(detail.decision_at) }}
              </p>
              <p v-if="detail.decision_reason" class="text-body-2">
                <strong>Motivo:</strong> {{ detail.decision_reason }}
              </p>
            </v-card-text>

            <v-divider />

            <v-card-actions class="flex-wrap pa-4">
              <v-btn
                v-if="!detail.assigned_admin_id && detail.status === 'submitted'"
                color="primary"
                variant="tonal"
                :loading="actionLoading"
                @click="assignRequest"
              >
                Asignarme
              </v-btn>

              <v-btn
                v-if="detail.status === 'under_review' || detail.status === 'submitted'"
                color="warning"
                variant="tonal"
                :loading="actionLoading"
                @click="correctionDialog = true"
              >
                Solicitar Corrección
              </v-btn>

              <v-btn
                v-if="detail.status === 'under_review'"
                color="error"
                variant="tonal"
                :loading="actionLoading"
                @click="rejectDialog = true"
              >
                Rechazar
              </v-btn>

              <v-btn
                v-if="detail.status === 'under_review'"
                color="success"
                variant="flat"
                :loading="actionLoading"
                :disabled="!canApprove"
                :title="!canApprove ? 'Primero debe aprobar el título' : 'Aprobar solicitud'"
                @click="approveRequest"
              >
                Aprobar Solicitud
              </v-btn>
            </v-card-actions>

            <v-alert v-if="detail.status === 'under_review' && !canApprove" type="info" class="ma-4" variant="tonal">
              <v-icon start size="small">mdi-information</v-icon>
              Debe aprobar el documento de <strong>Título Profesional</strong> antes de aprobar la solicitud.
            </v-alert>
          </v-card>
        </v-col>

        <v-col cols="12" lg="8">
          <h3 class="text-h6 mb-4">Documentos ({{ detail.documents.length }})</h3>

          <v-card v-if="detail.documents.length === 0" class="text-center pa-8 mb-4">
            <v-icon size="48" color="grey">mdi-file-document-outline</v-icon>
            <p class="mt-2">No hay documentos</p>
          </v-card>

          <v-card v-for="doc in detail.documents" :key="doc.id" rounded="xl" class="mb-4">
            <v-card-item>
              <template #prepend>
                <v-avatar :color="reviewStatusColors[doc.review_status]" size="40">
                  <v-icon color="white">
                    {{
                      doc.review_status === 'approved' ? 'mdi-check'
                        : doc.review_status === 'rejected' ? 'mdi-close'
                        : 'mdi-clock-outline'
                    }}
                  </v-icon>
                </v-avatar>
              </template>
              <v-card-title class="text-body-1">
                {{ documentTypeLabels[doc.document_type] ?? doc.document_type }}
              </v-card-title>
              <v-card-subtitle>
                {{ doc.original_filename }} • {{ doc.mime_type }}
              </v-card-subtitle>
            </v-card-item>

            <v-card-text>
              <div class="d-flex flex-wrap ga-2 mb-3">
                <v-chip :color="reviewStatusColors[doc.review_status]" variant="flat" size="small">
                  {{ doc.review_status }}
                </v-chip>
                <v-chip variant="outlined" size="small">
                  <v-icon start size="small">mdi-upload</v-icon>
                  {{ formatDate(doc.uploaded_at) }}
                </v-chip>
              </div>

              <p v-if="doc.review_notes" class="text-body-2">
                <strong>Notas:</strong> {{ doc.review_notes }}
              </p>

              <p class="text-caption text-medium-emphasis">
                SHA256: {{ doc.sha256.substring(0, 16) }}...
              </p>

              <div class="d-flex ga-2 mt-3">
                <v-btn
                  :href="`http://localhost:8000/api/v1${doc.download_url}`"
                  target="_blank"


                  color="primary"
                  variant="tonal"
                  size="small"
                >
                  <v-icon start size="small">mdi-download</v-icon>
                  Descargar PDF
                </v-btn>
              </div>
            </v-card-text>

            <v-divider v-if="detail.status === 'under_review'" />

            <v-card-actions v-if="(detail.status === 'under_review' || detail.status === 'submitted') && doc.review_status === 'pending'">

              <v-btn
                color="success"
                variant="tonal"
                size="small"
                :loading="actionLoading"
                @click="approveDocument(doc)"
              >
                <v-icon start size="small">mdi-check</v-icon>
                Aprobar
              </v-btn>
              <v-btn
                color="error"
                variant="tonal"
                size="small"
                :loading="actionLoading"
                @click="rejectReason = ''; rejectDialog = true"
              >
                <v-icon start size="small">mdi-close</v-icon>
                Rechazar
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <v-dialog v-model="rejectDialog" max-width="500">
      <v-card>
        <v-card-title>Rechazar</v-card-title>
        <v-card-text>
          <v-textarea
            v-model="rejectReason"
            label="Motivo del rechazo"
            placeholder="Ingrese el motivo..."
            rows="3"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="rejectDialog = false">Cancelar</v-btn>
          <v-btn color="error" variant="flat" :loading="actionLoading" @click="rejectRequest">Rechazar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="correctionDialog" max-width="500">
      <v-card>
        <v-card-title>Solicitar Corrección</v-card-title>
        <v-card-text>
          <v-textarea
            v-model="correctionReason"
            label="Motivo de la corrección"
            placeholder="¿Qué debe corregir el profesional?"
            rows="3"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="correctionDialog = false">Cancelar</v-btn>
          <v-btn color="warning" variant="flat" :loading="actionLoading" @click="requestCorrection">
            Solicitar Corrección
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
