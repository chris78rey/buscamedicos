<script setup lang="ts">
definePageMeta({
  layout: 'professional',
  middleware: ['auth', 'role'],
  roles: ['professional'],
})

const config = useRuntimeConfig()
const { 
  getProfessionalMe, 
  updateProfessionalMe, 
  getProfessionalVerificationStatus,
  uploadProfessionalDocument,
  deleteProfessionalDocument,
  submitProfessionalVerification
} = useApi()

const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const submitting = ref(false)

const profile = ref({
  public_display_name: '',
  professional_type: '',
  public_bio: '',
  years_experience: 0,
  languages: [] as string[],
})

const verificationStatus = ref<any>(null)
const documents = ref<any[]>([])

const docTypes = [
  { title: 'Cédula (Frente)', value: 'national_id_front' },
  { title: 'Cédula (Reverso)', value: 'national_id_back' },
  { title: 'Título / Diploma', value: 'degree' },
  { title: 'Certificado de Registro', value: 'registration_certificate' },
  { title: 'Selfie de verificación', value: 'selfie_verification' },
  { title: 'Hoja de vida', value: 'cv' },
  { title: 'Acuerdo firmado', value: 'signed_agreement' },
  { title: 'Documento de respaldo', value: 'supporting_document' },
]

const documentTypeLabels: Record<string, string> = {
  national_id_front: 'Cédula (Frente)',
  national_id_back: 'Cédula (Reverso)',
  degree: 'Título / Diploma',
  registration_certificate: 'Certificado de Registro',
  selfie_verification: 'Selfie de verificación',
  cv: 'Hoja de vida',
  signed_agreement: 'Acuerdo firmado',
  supporting_document: 'Documento de respaldo',
}


const selectedDocType = ref('degree')
const fileToUpload = ref<File | null>(null)

async function loadData() {
  loading.value = true
  try {
    const [me, status] = await Promise.all([
      getProfessionalMe(),
      getProfessionalVerificationStatus()
    ])
    profile.value = {
      public_display_name: me.public_display_name || '',
      professional_type: me.professional_type || '',
      public_bio: me.bio_public || '',
      years_experience: me.years_experience || 0,
      languages: me.languages || [],
    }

    verificationStatus.value = status
    documents.value = status.documents || []
  } catch (e) {
    console.error('Error loading profile data', e)
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  saving.value = true
  try {
    await updateProfessionalMe({
      public_display_name: profile.value.public_display_name,
      professional_type: profile.value.professional_type,
      bio_public: profile.value.public_bio,
      years_experience: profile.value.years_experience,
      languages: profile.value.languages,
    })

    // Refresh data
    await loadData()
  } catch (e) {
    console.error('Error saving profile', e)
  } finally {
    saving.value = false
  }
}

async function handleFileUpload() {
  if (!fileToUpload.value) return
  
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', fileToUpload.value)
    formData.append('document_type', selectedDocType.value)
    
    await uploadProfessionalDocument(formData)
    fileToUpload.value = null
    await loadData()
  } catch (e) {
    console.error('Error uploading document', e)
  } finally {
    uploading.value = false
  }
}

async function removeDocument(id: string) {
  if (!confirm('¿Seguro que desea eliminar este documento?')) return
  
  try {
    await deleteProfessionalDocument(id)
    await loadData()
  } catch (e) {
    console.error('Error deleting document', e)
  }
}

async function submitVerification() {
  submitting.value = true
  try {
    await submitProfessionalVerification()
    await loadData()
  } catch (e) {
    console.error('Error submitting verification', e)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadData()
})

function getStatusColor(status: string | null | undefined) {
  switch (status) {
    case 'approved':
      return 'success'
    case 'rejected':
      return 'error'
    case 'submitted':
    case 'under_review':
    case 'pending':
      return 'warning'
    case 'needs_correction':
      return 'info'
    case 'draft':
      return 'grey'
    case 'suspended':
      return 'error'
    default:
      return 'grey'
  }
}


function getStatusText(status: string | null | undefined) {
  switch (status) {
    case 'approved':
      return 'Aprobado'
    case 'rejected':
      return 'Rechazado'
    case 'submitted':
      return 'Enviado'
    case 'under_review':
      return 'En revisión'
    case 'pending':
      return 'Pendiente'
    case 'needs_correction':
      return 'Corrección requerida'
    case 'draft':
      return 'Borrador'
    case 'suspended':
      return 'Suspendido'
    case null:
    case undefined:
    case '':
      return 'Sin enviar'
    default:
      return status
  }
}

</script>

<template>
  <v-container>
    <v-row>
      <!-- A. Perfil Mínimo -->
      <v-col cols="12" md="6">
        <v-card rounded="xl" elevation="2">
          <v-card-item title="Perfil Público">
            <template #prepend>
              <v-icon icon="mdi-account" color="primary"></v-icon>
            </template>
          </v-card-item>
          <v-divider></v-divider>
          <v-card-text>
            <v-form @submit.prevent="saveProfile">
              <v-text-field
                v-model="profile.public_display_name"
                label="Nombre público (Ej: Dr. Juan Pérez)"
                variant="outlined"
                density="comfortable"
              ></v-text-field>
              
              <v-text-field
                v-model="profile.professional_type"
                label="Tipo profesional (Ej: Médico, Psicólogo)"
                variant="outlined"
                density="comfortable"
              ></v-text-field>
              
              <v-textarea
                v-model="profile.public_bio"
                label="Biografía / Resumen"
                variant="outlined"
                density="comfortable"
                rows="3"
              ></v-textarea>
              
              <v-text-field
                v-model.number="profile.years_experience"
                label="Años de experiencia"
                type="number"
                variant="outlined"
                density="comfortable"
              ></v-text-field>

              <p class="text-caption mb-2">Idiomas (Separa por comas)</p>
              <v-combobox
                v-model="profile.languages"
                label="Idiomas"
                multiple
                chips
                variant="outlined"
                density="comfortable"
              ></v-combobox>
              
              <v-btn
                color="primary"
                type="submit"
                :loading="saving"
                block
                class="mt-4"
                rounded="lg"
              >
                Guardar cambios
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- C. Estado de Validación -->
      <v-col cols="12" md="6">
        <v-card rounded="xl" elevation="2" class="mb-6">
          <v-card-item title="Estado de Validación">
            <template #prepend>
              <v-icon icon="mdi-shield-check" color="primary"></v-icon>
            </template>
          </v-card-item>
          <v-divider></v-divider>
          <v-card-text v-if="verificationStatus">
            <div class="d-flex justify-space-between align-center mb-4">
              <span class="text-subtitle-1">Estado Profesional:</span>
              <v-chip :color="getStatusColor(verificationStatus.professional_status)" size="small">
                {{ getStatusText(verificationStatus.professional_status) }}
              </v-chip>
            </div>
            
            <div class="d-flex justify-space-between align-center mb-4">
              <span class="text-subtitle-1">Onboarding:</span>
              <v-chip variant="outlined" size="small">
                {{ verificationStatus.onboarding_status }}
              </v-chip>
            </div>

            <div class="d-flex justify-space-between align-center mb-4">
              <span class="text-subtitle-1">Solicitud:</span>
              <v-chip :color="getStatusColor(verificationStatus.request_status)" size="small">
                {{ getStatusText(verificationStatus.request_status || 'Sin enviar') }}
              </v-chip>
            </div>

            <v-alert
              v-if="verificationStatus.decision_reason"
              type="info"
              variant="tonal"
              density="compact"
              class="mb-4"
            >
              {{ verificationStatus.decision_reason }}
            </v-alert>

            <v-btn
              v-if="[null, 'needs_correction', 'rejected'].includes(verificationStatus.request_status)"

              color="success"
              block
              :loading="submitting"
              @click="submitVerification"
              rounded="lg"
            >
              Enviar a validación
            </v-btn>
          </v-card-text>
          <v-card-text v-else class="text-center py-8">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
          </v-card-text>
        </v-card>

        <!-- B. Carga de Documentos -->
        <v-card rounded="xl" elevation="2">
          <v-card-item title="Carga de Documentos">
            <template #prepend>
              <v-icon icon="mdi-file-upload" color="primary"></v-icon>
            </template>
          </v-card-item>
          <v-divider></v-divider>
          <v-card-text>
            <v-select
              v-model="selectedDocType"
              :items="docTypes"
              label="Tipo de documento"
              variant="outlined"
              density="comfortable"
            ></v-select>
            
            <v-file-input
              v-model="fileToUpload"
              label="Seleccionar archivo"
              variant="outlined"
              density="comfortable"
              :accept="selectedDocType === 'degree' ? 'application/pdf' : '*'"
              prepend-icon="mdi-paperclip"
            >
              <template #append-inner v-if="selectedDocType === 'degree'">
                <v-tooltip activator="parent" location="top">Solo PDF para títulos</v-tooltip>
                <v-icon icon="mdi-information-outline" size="small"></v-icon>
              </template>
            </v-file-input>

            <v-btn
              color="primary"
              variant="tonal"
              block
              :disabled="!fileToUpload"
              :loading="uploading"
              @click="handleFileUpload"
              rounded="lg"
            >
              Cargar documento
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Tabla de documentos -->
      <v-col cols="12">
        <v-card rounded="xl" elevation="2">
          <v-card-item title="Mis Documentos"></v-card-item>
          <v-divider></v-divider>
          <v-table>
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Nombre</th>
                <th>Estado</th>
                <th>Notas</th>
                <th class="text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="doc in documents" :key="doc.id">
                <td>{{ documentTypeLabels[doc.document_type] || doc.document_type }}</td>

                <td>{{ doc.original_filename }}</td>
                <td>
                  <v-chip :color="getStatusColor(doc.review_status)" size="x-small">
                    {{ getStatusText(doc.review_status) }}
                  </v-chip>
                </td>
                <td><small>{{ doc.review_notes || '-' }}</small></td>
                <td class="text-right">
                  <v-btn
                    icon="mdi-download"
                    variant="text"
                    size="small"
                    color="primary"
                    :href="config.public.apiBase + doc.download_url"

                    target="_blank"
                  ></v-btn>
                  <v-btn
                    icon="mdi-delete"
                    variant="text"
                    size="small"
                    color="error"
                    @click="removeDocument(doc.id)"
                    :disabled="doc.review_status === 'approved'"
                  ></v-btn>
                </td>
              </tr>
              <tr v-if="documents.length === 0">
                <td colspan="5" class="text-center py-4 text-medium-emphasis">
                  No hay documentos cargados.
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>
