<script setup lang="ts">
import { FetchError } from 'ofetch'

import {
  useProfessionalAgenda,
  type ProfessionalAvailabilityItem,
  type ProfessionalTimeBlockItem,
  type ProfessionalModalityItem,
} from '~/composables/useProfessionalAgenda'

definePageMeta({
  layout: 'professional',
  middleware: ['auth', 'role'],
  roles: ['professional'],
})

const {
  getProfessionalMe,
  updateProfessionalMe,
  getMyPublicProfile,
  updateMyPublicProfile,
  getMyAvailabilities,
  createAvailability,
  updateAvailability,
  deleteAvailability,
  getMyTimeBlocks,
  createTimeBlock,
  updateTimeBlock,
  deleteTimeBlock,
  getMyModalities,
} = useProfessionalAgenda()

const loadingAll = ref(false)
const savingProfile = ref(false)
const savingAvailability = ref(false)
const savingBlock = ref(false)
const deletingAvailabilityId = ref<string | null>(null)
const deletingBlockId = ref<string | null>(null)

const errorMessage = ref('')
const successMessage = ref('')

const professionalForm = reactive({
  public_display_name: '',
})

const profileForm = reactive({
  public_title: '',
  public_bio: '',
  consultation_price: null as number | null,
  province: '',
  city: '',
  sector: '',
  years_experience: null as number | null,
  languages_json: '',
  is_public: false,
})

const availabilityForm = reactive({
  weekday: 0,
  modality_code: 'in_person_consultorio',
  start_time: '08:00',
  end_time: '12:00',
  slot_minutes: 30,
})

const timeBlockForm = reactive({
  starts_at: '',
  ends_at: '',
  reason: '',
  block_type: 'manual_block',
})

const editingAvailabilityId = ref<string | null>(null)
const editingBlockId = ref<string | null>(null)

const availabilities = ref<ProfessionalAvailabilityItem[]>([])
const timeBlocks = ref<ProfessionalTimeBlockItem[]>([])
const modalityOptions = ref<ProfessionalModalityItem[]>([
  { id: 'fallback-in-person', code: 'in_person_consultorio', name: 'Consulta presencial' },
  { id: 'fallback-tele', code: 'teleconsulta', name: 'Teleconsulta' },
])



const weekdayOptions = [
  { title: 'Lunes', value: 0 },
  { title: 'Martes', value: 1 },
  { title: 'Miércoles', value: 2 },
  { title: 'Jueves', value: 3 },
  { title: 'Viernes', value: 4 },
  { title: 'Sábado', value: 5 },
  { title: 'Domingo', value: 6 },
]

const slotMinuteOptions = [15, 20, 30, 45, 60].map(value => ({
  title: `${value} minutos`,
  value,
}))

function resolveError(error: unknown, fallback: string) {
  if (error instanceof FetchError) {
    return error.data?.detail?.toString() || fallback
  }
  return fallback
}

function clearMessages() {
  errorMessage.value = ''
  successMessage.value = ''
}

function formatWeekday(value: number) {
  return weekdayOptions.find(item => item.value === value)?.title || `Día ${value}`
}

function formatDateTime(value?: string | null) {
  if (!value) return 'N/A'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleString('es-EC', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function toLocalDateTimeInputValue(value?: string | null) {
  if (!value) return ''
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return ''
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())}T${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`
}

function toBackendDateTime(value: string) {
  if (!value) return ''
  return value.length === 16 ? `${value}:00` : value
}

function resetAvailabilityForm() {
  availabilityForm.weekday = 0
  availabilityForm.modality_code = modalityOptions.value[0]?.code || 'in_person_consultorio'
  availabilityForm.start_time = '08:00'
  availabilityForm.end_time = '12:00'
  availabilityForm.slot_minutes = 30
  editingAvailabilityId.value = null
}

function resetTimeBlockForm() {
  timeBlockForm.starts_at = ''
  timeBlockForm.ends_at = ''
  timeBlockForm.reason = ''
  timeBlockForm.block_type = 'manual_block'
  editingBlockId.value = null
}

async function loadAll() {
  loadingAll.value = true
  clearMessages()

  try {
    const [
      professional,
      profile,
      availabilityRows,
      blockRows,
      modalityRows,
    ] = await Promise.all([
      getProfessionalMe(),
      getMyPublicProfile(),
      getMyAvailabilities(),
      getMyTimeBlocks(),
      getMyModalities().catch(() => modalityOptions.value),
    ])

    professionalForm.public_display_name = professional.public_display_name || ''

    profileForm.public_title = profile.public_title || ''
    profileForm.public_bio = profile.public_bio || ''
    profileForm.consultation_price = profile.consultation_price ?? null
    profileForm.province = profile.province || ''
    profileForm.city = profile.city || ''
    profileForm.sector = profile.sector || ''
    profileForm.years_experience = profile.years_experience ?? null
    profileForm.languages_json = profile.languages_json || ''
    profileForm.is_public = Boolean(profile.is_public)

    availabilities.value = availabilityRows
    timeBlocks.value = blockRows
    modalityOptions.value = modalityRows.length ? modalityRows : modalityOptions.value

    if (!availabilityForm.modality_code && modalityOptions.value.length) {
      availabilityForm.modality_code = modalityOptions.value[0].code
    }
  }
  catch (error: unknown) {
    errorMessage.value = resolveError(error, 'No se pudo cargar la configuración operativa del profesional.')
  }
  finally {
    loadingAll.value = false
  }
}

async function handleSaveProfile() {
  savingProfile.value = true
  clearMessages()

  try {
    await updateProfessionalMe({
      public_display_name: professionalForm.public_display_name || null,
    })

    await updateMyPublicProfile({
      public_title: profileForm.public_title,
      public_bio: profileForm.public_bio || null,
      consultation_price: profileForm.consultation_price,
      province: profileForm.province || null,
      city: profileForm.city || null,
      sector: profileForm.sector || null,
      years_experience: profileForm.years_experience,
      languages_json: profileForm.languages_json || null,
      is_public: profileForm.is_public,
    })

    successMessage.value = 'Perfil y configuración pública guardados correctamente.'
  }
  catch (error: unknown) {
    errorMessage.value = resolveError(error, 'No se pudo guardar el perfil público.')
  }
  finally {
    savingProfile.value = false
  }
}

async function handleSaveAvailability() {
  savingAvailability.value = true
  clearMessages()

  try {
    const payload = {
      weekday: availabilityForm.weekday,
      modality_code: availabilityForm.modality_code,
      start_time: availabilityForm.start_time,
      end_time: availabilityForm.end_time,
      slot_minutes: availabilityForm.slot_minutes,
    }

    let saved: ProfessionalAvailabilityItem
    if (editingAvailabilityId.value) {
      saved = await updateAvailability(editingAvailabilityId.value, payload)
      availabilities.value = availabilities.value.map(item =>
        item.id === saved.id ? saved : item,
      )
      successMessage.value = 'Disponibilidad actualizada correctamente.'
    }
    else {
      saved = await createAvailability(payload)
      availabilities.value.push(saved)
      successMessage.value = 'Disponibilidad creada correctamente.'
    }

    availabilities.value = [...availabilities.value].sort((a, b) => {
      if (a.weekday !== b.weekday) return a.weekday - b.weekday
      return a.start_time.localeCompare(b.start_time)
    })

    resetAvailabilityForm()
  }
  catch (error: unknown) {
    errorMessage.value = resolveError(error, 'No se pudo guardar la disponibilidad.')
  }
  finally {
    savingAvailability.value = false
  }
}

function editAvailability(item: ProfessionalAvailabilityItem) {
  availabilityForm.weekday = item.weekday
  availabilityForm.modality_code = item.modality_code
  availabilityForm.start_time = item.start_time.slice(0, 5)
  availabilityForm.end_time = item.end_time.slice(0, 5)
  availabilityForm.slot_minutes = item.slot_minutes
  editingAvailabilityId.value = item.id
}

async function handleDeleteAvailability(id: string) {
  deletingAvailabilityId.value = id
  clearMessages()

  try {
    await deleteAvailability(id)
    availabilities.value = availabilities.value.filter(item => item.id !== id)
    if (editingAvailabilityId.value === id) {
      resetAvailabilityForm()
    }
    successMessage.value = 'Disponibilidad eliminada correctamente.'
  }
  catch (error: unknown) {
    errorMessage.value = resolveError(error, 'No se pudo eliminar la disponibilidad.')
  }
  finally {
    deletingAvailabilityId.value = null
  }
}

async function handleSaveTimeBlock() {
  savingBlock.value = true
  clearMessages()

  try {
    const payload = {
      starts_at: toBackendDateTime(timeBlockForm.starts_at),
      ends_at: toBackendDateTime(timeBlockForm.ends_at),
      reason: timeBlockForm.reason || null,
      block_type: timeBlockForm.block_type,
    }

    let saved: ProfessionalTimeBlockItem
    if (editingBlockId.value) {
      saved = await updateTimeBlock(editingBlockId.value, payload)
      timeBlocks.value = timeBlocks.value.map(item => item.id === saved.id ? saved : item)
      successMessage.value = 'Bloqueo actualizado correctamente.'
    }
    else {
      saved = await createTimeBlock(payload)
      timeBlocks.value.unshift(saved)
      successMessage.value = 'Bloqueo creado correctamente.'
    }

    timeBlocks.value = [...timeBlocks.value].sort((a, b) => {
      return new Date(b.starts_at).getTime() - new Date(a.starts_at).getTime()
    })

    resetTimeBlockForm()
  }
  catch (error: unknown) {
    errorMessage.value = resolveError(error, 'No se pudo guardar el bloqueo.')
  }
  finally {
    savingBlock.value = false
  }
}

function editTimeBlock(item: ProfessionalTimeBlockItem) {
  timeBlockForm.starts_at = toLocalDateTimeInputValue(item.starts_at)
  timeBlockForm.ends_at = toLocalDateTimeInputValue(item.ends_at)
  timeBlockForm.reason = item.reason || ''
  timeBlockForm.block_type = item.block_type || 'manual_block'
  editingBlockId.value = item.id
}

async function handleDeleteTimeBlock(id: string) {
  deletingBlockId.value = id
  clearMessages()

  try {
    await deleteTimeBlock(id)
    timeBlocks.value = timeBlocks.value.filter(item => item.id !== id)
    if (editingBlockId.value === id) {
      resetTimeBlockForm()
    }
    successMessage.value = 'Bloqueo eliminado correctamente.'
  }
  catch (error: unknown) {
    errorMessage.value = resolveError(error, 'No se pudo eliminar el bloqueo.')
  }
  finally {
    deletingBlockId.value = null
  }
}

onMounted(() => {
  loadAll()
})
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h2 class="text-h5 font-weight-bold">Perfil y agenda</h2>
        <p class="text-body-2 text-medium-emphasis mb-0">
          Desde esta pantalla se configura lo necesario para que las reservas públicas funcionen de forma real.
        </p>
      </div>

      <v-btn
        color="primary"
        prepend-icon="mdi-refresh"
        variant="tonal"
        :loading="loadingAll"
        @click="loadAll"
      >
        Recargar
      </v-btn>
    </div>

    <v-alert
      v-if="errorMessage"
      class="mb-4"
      type="error"
      variant="tonal"
    >
      {{ errorMessage }}
    </v-alert>

    <v-alert
      v-if="successMessage"
      class="mb-4"
      type="success"
      variant="tonal"
    >
      {{ successMessage }}
    </v-alert>

    <v-row>
      <v-col cols="12" lg="6">
        <v-card rounded="xl">
          <v-card-item prepend-icon="mdi-account-card-outline">
            <v-card-title>Perfil público</v-card-title>
            <v-card-subtitle>
              Esta información alimenta la búsqueda pública y el detalle del profesional.
            </v-card-subtitle>
          </v-card-item>

          <v-card-text class="d-flex flex-column ga-4">
            <v-text-field
              v-model="professionalForm.public_display_name"
              label="Nombre público"
              variant="outlined"
            />

            <v-text-field
              v-model="profileForm.public_title"
              label="Título público"
              variant="outlined"
            />

            <v-textarea
              v-model="profileForm.public_bio"
              label="Biografía pública"
              rows="5"
              variant="outlined"
            />

            <v-text-field
              v-model.number="profileForm.consultation_price"
              label="Precio referencial público (USD)"
              type="number"
              min="0"
              step="0.01"
              variant="outlined"
            />

            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="profileForm.province"
                  label="Provincia"
                  variant="outlined"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="profileForm.city"
                  label="Ciudad"
                  variant="outlined"
                />
              </v-col>
            </v-row>

            <v-text-field
              v-model="profileForm.sector"
              label="Sector"
              variant="outlined"
            />

            <v-text-field
              v-model.number="profileForm.years_experience"
              label="Años de experiencia"
              type="number"
              min="0"
              variant="outlined"
            />

            <v-text-field
              v-model="profileForm.languages_json"
              label="Idiomas visibles"
              hint="Ejemplo: español, inglés"
              persistent-hint
              variant="outlined"
            />

            <v-switch
              v-model="profileForm.is_public"
              color="primary"
              inset
              label="Publicar perfil en búsqueda"
            />
          </v-card-text>

          <v-card-actions>
            <v-spacer />
            <v-btn
              color="primary"
              :loading="savingProfile"
              prepend-icon="mdi-content-save-outline"
              @click="handleSaveProfile"
            >
              Guardar perfil
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" lg="6">
        <v-card rounded="xl" class="mb-6">
          <v-card-item prepend-icon="mdi-calendar-clock-outline">
            <v-card-title>Disponibilidad semanal</v-card-title>
            <v-card-subtitle>
              Estos horarios generan los slots públicos para reserva.
            </v-card-subtitle>
          </v-card-item>

          <v-card-text class="d-flex flex-column ga-4">
            <v-row>
              <v-col cols="12" md="6">
                <v-select
                  v-model="availabilityForm.weekday"
                  :items="weekdayOptions"
                  item-title="title"
                  item-value="value"
                  label="Día"
                  variant="outlined"
                />
              </v-col>

              <v-col cols="12" md="6">
                <v-select
                  v-model="availabilityForm.modality_code"
                  :items="modalityOptions"
                  item-title="name"
                  item-value="code"
                  label="Modalidad"
                  variant="outlined"
                />
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="availabilityForm.start_time"
                  label="Hora inicio"
                  type="time"
                  variant="outlined"
                />
              </v-col>

              <v-col cols="12" md="4">
                <v-text-field
                  v-model="availabilityForm.end_time"
                  label="Hora fin"
                  type="time"
                  variant="outlined"
                />
              </v-col>

              <v-col cols="12" md="4">
                <v-select
                  v-model="availabilityForm.slot_minutes"
                  :items="slotMinuteOptions"
                  item-title="title"
                  item-value="value"
                  label="Duración slot"
                  variant="outlined"
                />
              </v-col>
            </v-row>
          </v-card-text>

          <v-card-actions>
            <v-btn
              v-if="editingAvailabilityId"
              variant="text"
              @click="resetAvailabilityForm"
            >
              Cancelar edición
            </v-btn>

            <v-spacer />

            <v-btn
              color="primary"
              :loading="savingAvailability"
              prepend-icon="mdi-content-save-outline"
              @click="handleSaveAvailability"
            >
              {{ editingAvailabilityId ? 'Actualizar disponibilidad' : 'Agregar disponibilidad' }}
            </v-btn>
          </v-card-actions>
        </v-card>

        <v-card rounded="xl">
          <v-card-item prepend-icon="mdi-format-list-bulleted-square">
            <v-card-title>Disponibilidades actuales</v-card-title>
          </v-card-item>

          <v-card-text v-if="!availabilities.length" class="text-medium-emphasis">
            No existen disponibilidades cargadas todavía.
          </v-card-text>

          <v-list v-else lines="two">
            <v-list-item
              v-for="item in availabilities"
              :key="item.id"
            >
              <template #title>
                {{ formatWeekday(item.weekday) }} · {{ item.modality_code }}
              </template>

              <template #subtitle>
                {{ item.start_time }} - {{ item.end_time }} · {{ item.slot_minutes }} min
              </template>

              <template #append>
                <div class="d-flex ga-2">
                  <v-btn
                    size="small"
                    variant="tonal"
                    color="primary"
                    prepend-icon="mdi-pencil-outline"
                    @click="editAvailability(item)"
                  >
                    Editar
                  </v-btn>

                  <v-btn
                    size="small"
                    variant="tonal"
                    color="error"
                    prepend-icon="mdi-delete-outline"
                    :loading="deletingAvailabilityId === item.id"
                    @click="handleDeleteAvailability(item.id)"
                  >
                    Eliminar
                  </v-btn>
                </div>
              </template>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>

    <v-card rounded="xl" class="mt-6">
      <v-card-item prepend-icon="mdi-calendar-remove-outline">
        <v-card-title>Bloqueos puntuales</v-card-title>
        <v-card-subtitle>
          Sirven para vacaciones, ausencias, reuniones o cierres parciales de agenda.
        </v-card-subtitle>
      </v-card-item>

      <v-card-text class="d-flex flex-column ga-4">
        <v-row>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="timeBlockForm.starts_at"
              label="Inicio"
              type="datetime-local"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-text-field
              v-model="timeBlockForm.ends_at"
              label="Fin"
              type="datetime-local"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-text-field
              v-model="timeBlockForm.block_type"
              label="Tipo de bloqueo"
              variant="outlined"
            />
          </v-col>
        </v-row>

        <v-text-field
          v-model="timeBlockForm.reason"
          label="Motivo"
          variant="outlined"
        />
      </v-card-text>

      <v-card-actions>
        <v-btn
          v-if="editingBlockId"
          variant="text"
          @click="resetTimeBlockForm"
        >
          Cancelar edición
        </v-btn>

        <v-spacer />

        <v-btn
          color="primary"
          :loading="savingBlock"
          prepend-icon="mdi-content-save-outline"
          @click="handleSaveTimeBlock"
        >
          {{ editingBlockId ? 'Actualizar bloqueo' : 'Agregar bloqueo' }}
        </v-btn>
      </v-card-actions>

      <v-divider class="my-2" />

      <v-card-text v-if="!timeBlocks.length" class="text-medium-emphasis">
        No existen bloqueos puntuales cargados.
      </v-card-text>

      <v-list v-else lines="two">
        <v-list-item
          v-for="item in timeBlocks"
          :key="item.id"
        >
          <template #title>
            {{ item.block_type }}
          </template>

          <template #subtitle>
            {{ formatDateTime(item.starts_at) }} → {{ formatDateTime(item.ends_at) }}
            <span v-if="item.reason">· {{ item.reason }}</span>
          </template>

          <template #append>
            <div class="d-flex ga-2">
              <v-btn
                size="small"
                variant="tonal"
                color="primary"
                prepend-icon="mdi-pencil-outline"
                @click="editTimeBlock(item)"
              >
                Editar
              </v-btn>

              <v-btn
                size="small"
                variant="tonal"
                color="error"
                prepend-icon="mdi-delete-outline"
                :loading="deletingBlockId === item.id"
                @click="handleDeleteTimeBlock(item.id)"
              >
                Eliminar
              </v-btn>
            </div>
          </template>
        </v-list-item>
      </v-list>
    </v-card>
  </div>
</template>
