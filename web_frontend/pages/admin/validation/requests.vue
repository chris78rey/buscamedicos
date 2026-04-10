<script setup lang="ts">
import type { AdminVerificationRequest, AdminVerificationRequestDetail } from '~/types/verification'

definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_validation'],
})

const {
  apiFetch,
  getAdminVerificationRequests,
  getAdminVerificationRequest,
  assignAdminVerificationRequest,
  approveAdminVerificationDocument,
  rejectAdminVerificationDocument,
  approveAdminVerification,
  rejectAdminVerification,
  requestCorrectionAdminVerification,
} = useApi()

const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const loading = ref(false)
const detailLoading = ref(false)
const processing = ref(false)
const requests = ref<AdminVerificationRequest[]>([])
const selectedRequest = ref<AdminVerificationRequestDetail | null>(null)
const showDetail = ref(false)

// Forms
const notes = ref('')
const rejectionReason = ref('')
const correctionReason = ref('')

async function loadRequests() {
  loading.value = true
  try {
    requests.value = await getAdminVerificationRequests()
  } catch (e) {
    console.error('Error loading requests', e)
  } finally {
    loading.value = false
  }
}

async function openRequest(requestId: string) {
  detailLoading.value = true
  showDetail.value = true
  try {
    selectedRequest.value = await getAdminVerificationRequest(requestId)
    notes.value = ''
    rejectionReason.value = ''
    correctionReason.value = ''
  } catch (e) {
    console.error('Error loading request detail', e)
    showDetail.value = false
  } finally {
    detailLoading.value = false
  }
}

async function handleAssign(requestId: string) {
  processing.value = true
  try {
    await assignAdminVerificationRequest(requestId)
    await loadRequests()
    if (showDetail.value && selectedRequest.value?.id === requestId) {
      await openRequest(requestId)
    }
  } catch (e) {
    console.error('Error assigning request', e)
  } finally {
    processing.value = false
  }
}

async function handleApproveDoc(docId: string) {
  if (!selectedRequest.value) return
  processing.value = true
  try {
    await approveAdminVerificationDocument(selectedRequest.value.id, docId, notes.value)
    await openRequest(selectedRequest.value.id)
  } catch (e) {
    console.error('Error approving document', e)
  } finally {
    processing.value = false
  }
}

async function handleRejectDoc(docId: string) {
  if (!selectedRequest.value || !rejectionReason.value) {
    alert('Debe ingresar un motivo de rechazo')
    return
  }
  processing.value = true
  try {
    await rejectAdminVerificationDocument(selectedRequest.value.id, docId, rejectionReason.value)
    await openRequest(selectedRequest.value.id)
  } catch (e) {
    console.error('Error rejecting document', e)
  } finally {
    processing.value = false
  }
}

async function handleApproveRequest() {
  if (!selectedRequest.value) return
  if (!confirm('¿Seguro que desea aprobar esta solicitud?')) return
  
  processing.value = true
  try {
    await approveAdminVerification(selectedRequest.value.id)
    showDetail.value = false
    await loadRequests()
  } catch (e) {
    console.error('Error approving request', e)
  } finally {
    processing.value = false
  }
}

async function handleRejectRequest() {
  if (!selectedRequest.value || !rejectionReason.value) {
    alert('Debe ingresar un motivo de rechazo final')
    return
  }
  processing.value = true
  try {
    await rejectAdminVerification(selectedRequest.value.id, rejectionReason.value)
    showDetail.value = false
    await loadRequests()
  } catch (e) {
    console.error('Error rejecting request', e)
  } finally {
    processing.value = false
  }
}

async function handleCorrectionRequest() {
  if (!selectedRequest.value || !correctionReason.value) {
    alert('Debe ingresar un motivo para solicitar corrección')
    return
  }
  processing.value = true
  try {
    await requestCorrectionAdminVerification(selectedRequest.value.id, correctionReason.value)
    showDetail.value = false
    await loadRequests()
  } catch (e) {
    console.error('Error requesting correction', e)
  } finally {
    processing.value = false
  }
}

onMounted(() => {
  loadRequests()
})

function getStatusColor(status: string) {
  switch (status) {
    case 'approved': return 'success'
    case 'rejected': return 'error'
    case 'pending': return 'warning'
    case 'correction_requested': return 'info'
    default: return 'grey'
  }
}

const headers = [
  { title: 'Médico', key: 'professional_display_name' },
  { title: 'Estado', key: 'status' },
  { title: 'Fecha', key: 'submitted_at' },
  { title: 'Docs (A/P/R)', key: 'stats' },
  { title: 'Acciones', key: 'actions', align: 'end' },
]

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

function getFullDownloadUrl(url: string) {
  if (!url) return '#'
  // En desarrollo local, el API suele estar en el puerto 8000
  // Esta lógica asegura que salgamos del servidor de Nuxt (3000) hacia el backend (8000)
  const origin = window.location.origin.replace(':3000', ':8000')
  return `${origin}${url}`
}
</script>

<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card rounded="xl" elevation="2">
          <v-card-item title="Solicitudes de Validación Médica">
            <template #prepend>
              <v-icon icon="mdi-badge-account-horizontal" color="primary"></v-icon>
            </template>
            <template #append>
              <v-btn icon="mdi-refresh" variant="text" @click="loadRequests" :loading="loading"></v-btn>
            </template>
          </v-card-item>
          <v-divider></v-divider>
          
          <v-data-table
            :headers="headers"
            :items="requests"
            :loading="loading"
            hover
          >
            <template #item.status="{ item }">
              <v-chip :color="getStatusColor(item.status)" size="small">
                {{ item.status }}
              </v-chip>
            </template>
            <template #item.submitted_at="{ item }">
              {{ formatDate(item.submitted_at) }}
            </template>
            <template #item.stats="{ item }">
              <span class="text-success">{{ item.approved_count }}</span> /
              <span class="text-warning">{{ item.pending_count }}</span> /
              <span class="text-error">{{ item.rejected_count }}</span>
            </template>
            <template #item.actions="{ item }">
              <v-btn
                v-if="!item.assigned_admin_id"
                color="info"
                variant="text"
                size="small"
                @click="handleAssign(item.id)"
              >
                Asignar
              </v-btn>
              <v-btn
                color="primary"
                variant="tonal"
                size="small"
                @click="openRequest(item.id)"
                class="ml-2"
              >
                Ver detalle
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Diálogo de Detalle -->
    <v-dialog v-model="showDetail" fullscreen scrollable>
      <v-card v-if="selectedRequest" class="bg-grey-lighten-4">
        <v-toolbar color="primary">
          <v-btn icon="mdi-close" @click="showDetail = false"></v-btn>
          <v-toolbar-title>
            Validación: {{ selectedRequest.professional?.public_display_name || 'Médico' }}
          </v-toolbar-title>
          <v-spacer></v-spacer>
          <v-chip color="white" class="mr-4">{{ selectedRequest.status }}</v-chip>
        </v-toolbar>

        <v-card-text class="pa-6">
          <v-row>
            <!-- Info del Profesional -->
            <v-col cols="12" md="4">
              <v-card rounded="xl" class="mb-6">
                <v-card-item title="Información General"></v-card-item>
                <v-divider></v-divider>
                <v-card-text>
                  <p><strong>Nombre:</strong> {{ selectedRequest.person?.first_name }} {{ selectedRequest.person?.last_name }}</p>
                  <p><strong>Cédula:</strong> {{ selectedRequest.person?.national_id }}</p>
                  <p><strong>Email:</strong> {{ selectedRequest.professional?.email }}</p>
                  <p><strong>Tipo:</strong> {{ selectedRequest.professional?.professional_type }}</p>
                  <p><strong>Fecha Solicitud:</strong> {{ formatDate(selectedRequest.submitted_at) }}</p>
                </v-card-text>
              </v-card>

              <v-card rounded="xl">
                <v-card-item title="Acciones Finales"></v-card-item>
                <v-divider></v-divider>
                <v-card-text>
                  <v-textarea
                    v-model="rejectionReason"
                    label="Motivo de rechazo"
                    variant="outlined"
                    rows="2"
                    class="mb-4"
                  ></v-textarea>
                  
                  <div class="d-flex flex-column gap-2">
                    <v-btn
                      color="success"
                      block
                      @click="handleApproveRequest"
                      :loading="processing"
                      prepend-icon="mdi-check-decagram"
                    >
                      Aprobar Solicitud
                    </v-btn>
                    
                    <v-btn
                      color="error"
                      variant="outlined"
                      block
                      @click="handleRejectRequest"
                      :loading="processing"
                      class="mt-2"
                    >
                      Rechazar Solicitud
                    </v-btn>
                  </div>

                  <v-divider class="my-4"></v-divider>

                  <v-textarea
                    v-model="correctionReason"
                    label="Motivo de corrección"
                    variant="outlined"
                    rows="2"
                    class="mb-4"
                  ></v-textarea>
                  
                  <v-btn
                    color="info"
                    variant="tonal"
                    block
                    @click="handleCorrectionRequest"
                    :loading="processing"
                  >
                    Pedir Corrección
                  </v-btn>
                </v-card-text>
              </v-card>
            </v-col>

            <!-- Documentos -->
            <v-col cols="12" md="8">
              <v-card rounded="xl">
                <v-card-item title="Documentos Cargados"></v-card-item>
                <v-divider></v-divider>
                <v-card-text>
                  <v-expansion-panels>
                    <v-expansion-panel
                      v-for="doc in selectedRequest.documents"
                      :key="doc.id"
                    >
                      <v-expansion-panel-title>
                        <v-icon
                          :color="getStatusColor(doc.review_status)"
                          class="mr-2"
                        >
                          {{ doc.review_status === 'approved' ? 'mdi-check-circle' : 'mdi-file' }}
                        </v-icon>
                        {{ doc.document_type }} - {{ doc.original_filename }}
                        <v-spacer></v-spacer>
                        <v-chip size="x-small" :color="getStatusColor(doc.review_status)">
                          {{ doc.review_status }}
                        </v-chip>
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <div class="d-flex align-center mb-4">
                          <v-btn
                            color="primary"
                            prepend-icon="mdi-download"
                            :href="getFullDownloadUrl(doc.download_url)"
                            target="_blank"
                            variant="tonal"
                          >
                            Descargar / Ver PDF
                          </v-btn>
                          <span class="ml-4 text-caption text-medium-emphasis">
                            Subido el: {{ formatDate(doc.uploaded_at) }}
                          </span>
                        </div>

                        <v-divider class="mb-4"></v-divider>

                        <v-textarea
                          v-model="notes"
                          label="Notas de revisión (Opcional)"
                          variant="outlined"
                          rows="2"
                        ></v-textarea>

                        <div class="d-flex justify-end mt-2">
                          <v-btn
                            color="error"
                            variant="text"
                            @click="handleRejectDoc(doc.id)"
                            :loading="processing"
                            :disabled="doc.review_status === 'approved'"
                          >
                            Rechazar Doc
                          </v-btn>
                          <v-btn
                            color="success"
                            variant="tonal"
                            class="ml-2"
                            @click="handleApproveDoc(doc.id)"
                            :loading="processing"
                            :disabled="doc.review_status === 'approved'"
                          >
                            Aprobar Doc
                          </v-btn>
                        </div>
                        
                        <v-alert
                          v-if="doc.review_notes"
                          type="info"
                          variant="tonal"
                          class="mt-4"
                          density="compact"
                        >
                          <strong>Nota anterior:</strong> {{ doc.review_notes }}
                        </v-alert>
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
      <v-card v-else class="d-flex align-center justify-center" style="height: 100vh;">
        <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.gap-2 {
  gap: 8px;
}
</style>
