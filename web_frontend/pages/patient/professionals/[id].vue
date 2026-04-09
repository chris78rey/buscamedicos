<script setup lang="ts">
import { FetchError } from 'ofetch'

import type { AppointmentCreatedResponse } from '~/types/appointment'
import type {
  ProfessionalSpecialty,
  PublicProfessionalDetail,
  SlotItem,
} from '~/types/professional'

definePageMeta({
  layout: 'patient',
  middleware: ['auth', 'role'],
  roles: ['patient'],
})

const route = useRoute()
const router = useRouter()
const {
  createAppointment,
  getPublicProfessional,
  getSlots,
} = useApi()

const identifier = computed(() => String(route.params.id ?? ''))

const profile = ref<PublicProfessionalDetail | null>(null)
const slots = ref<SlotItem[]>([])
const loadingProfile = ref(false)
const loadingSlots = ref(false)
const profileError = ref('')
const slotsError = ref('')
const bookingError = ref('')
const bookingSuccess = ref<AppointmentCreatedResponse | null>(null)
const bookingInProgressFor = ref<string | null>(null)

const selectedDate = ref(getTodayDateInputValue())
const selectedModality = ref('in_person_consultorio')
const patientNote = ref('')

const modalityOptions = [
  { title: 'Consulta presencial', value: 'in_person_consultorio' },
  { title: 'Teleconsulta', value: 'teleconsulta' },
]

function getTodayDateInputValue() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function specialtyLabel(item: ProfessionalSpecialty) {
  return typeof item === 'string' ? item : item.name
}

function formatSpecialties(items: ProfessionalSpecialty[] | undefined) {
  if (!items?.length) {
    return 'Sin especialidades visibles'
  }

  return items.map(specialtyLabel).join(', ')
}

function formatCurrency(value?: number | null) {
  if (value === null || value === undefined) {
    return 'Precio no disponible'
  }

  return new Intl.NumberFormat('es-EC', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(value)
}

function formatLocation() {
  if (!profile.value) {
    return 'Ubicacion no disponible'
  }

  return [profile.value.city, profile.value.province, profile.value.sector]
    .filter(Boolean)
    .join(' · ') || 'Ubicacion no disponible'
}

function formatSlotDateTime(value: string) {
  const parsed = new Date(value)

  if (Number.isNaN(parsed.getTime())) {
    return value
  }

  return parsed.toLocaleString('es-EC', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

async function loadProfile() {
  loadingProfile.value = true
  profileError.value = ''

  try {
    profile.value = await getPublicProfessional(identifier.value)
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      profileError.value = error.data?.detail?.toString() || 'No se pudo cargar el perfil del profesional.'
    }
    else {
      profileError.value = 'Ocurrio un error inesperado al cargar el perfil.'
    }

    profile.value = null
  }
  finally {
    loadingProfile.value = false
  }
}

async function loadSlots() {
  if (!profile.value?.professional_id) {
    return
  }

  loadingSlots.value = true
  slotsError.value = ''

  try {
    slots.value = await getSlots(
      profile.value.professional_id,
      selectedDate.value,
      selectedModality.value,
    )
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      slotsError.value = error.data?.detail?.toString() || 'No se pudieron consultar los slots.'
    }
    else {
      slotsError.value = 'Ocurrio un error inesperado al cargar los slots.'
    }

    slots.value = []
  }
  finally {
    loadingSlots.value = false
  }
}

async function handleBook(slot: SlotItem) {
  if (!profile.value?.professional_id || !slot.is_available) {
    return
  }

  bookingError.value = ''
  bookingSuccess.value = null
  bookingInProgressFor.value = slot.start

  try {
    bookingSuccess.value = await createAppointment({
      professional_id: profile.value.professional_id,
      modality_code: selectedModality.value,
      scheduled_start: slot.start,
      patient_note: patientNote.value.trim() || undefined,
    })

    await loadSlots()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      bookingError.value = error.data?.detail?.toString() || 'No se pudo reservar la cita.'
    }
    else {
      bookingError.value = 'Ocurrio un error inesperado al reservar.'
    }
  }
  finally {
    bookingInProgressFor.value = null
  }
}

async function goToAppointments() {
  await router.push('/patient/appointments')
}

onMounted(async () => {
  await loadProfile()
  await loadSlots()
})

watch([selectedDate, selectedModality], async () => {
  if (profile.value?.professional_id) {
    await loadSlots()
  }
})
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <div class="d-flex flex-wrap ga-3">
      <v-btn
        prepend-icon="mdi-arrow-left"
        variant="text"
        @click="router.push('/patient/professionals')"
      >
        Volver a resultados
      </v-btn>

      <v-spacer />

      <v-btn
        color="primary"
        prepend-icon="mdi-calendar-check"
        variant="tonal"
        @click="goToAppointments"
      >
        Ir a mis citas
      </v-btn>
    </div>

    <v-alert
      v-if="profileError"
      type="error"
      variant="tonal"
    >
      {{ profileError }}
    </v-alert>

    <v-skeleton-loader
      v-else-if="loadingProfile"
      rounded="xl"
      type="heading, paragraph, paragraph, actions"
    />

    <template v-else-if="profile">
      <v-card rounded="xl">
        <v-card-item prepend-icon="mdi-account-heart-outline">
          <v-card-title class="text-h5">
            {{ profile.public_display_name }}
          </v-card-title>
          <v-card-subtitle>{{ profile.public_title }}</v-card-subtitle>
        </v-card-item>

        <v-card-text class="d-flex flex-column ga-4">
          <div>
            <div class="text-caption text-medium-emphasis">Especialidades</div>
            <div class="text-body-2">{{ formatSpecialties(profile.specialties) }}</div>
          </div>

          <div>
            <div class="text-caption text-medium-emphasis">Ubicacion</div>
            <div class="text-body-2">{{ formatLocation() }}</div>
          </div>

          <div>
            <div class="text-caption text-medium-emphasis">Experiencia</div>
            <div class="text-body-2">
              {{ profile.years_experience ?? 'No reportada' }}
            </div>
          </div>

          <div>
            <div class="text-caption text-medium-emphasis">Precio referencial</div>
            <div class="text-body-2">{{ formatCurrency(profile.consultation_price) }}</div>
          </div>

          <div v-if="profile.public_bio">
            <div class="text-caption text-medium-emphasis">Bio publica</div>
            <div class="text-body-2" style="white-space: pre-line;">
              {{ profile.public_bio }}
            </div>
          </div>
        </v-card-text>
      </v-card>

      <v-card rounded="xl">
        <v-card-item>
          <v-card-title class="text-h6">Seleccion de agenda</v-card-title>
          <v-card-subtitle>
            La reserva se realiza sobre slots disponibles del profesional.
          </v-card-subtitle>
        </v-card-item>

        <v-card-text>
          <v-alert
            v-if="bookingError"
            class="mb-4"
            type="error"
            variant="tonal"
          >
            {{ bookingError }}
          </v-alert>

          <v-alert
            v-if="bookingSuccess"
            class="mb-4"
            type="success"
            variant="tonal"
          >
            Cita creada con codigo {{ bookingSuccess.public_code }} para
            {{ formatSlotDateTime(bookingSuccess.scheduled_start) }}.
          </v-alert>

          <v-row>
            <v-col cols="12" md="4">
              <v-text-field
                v-model="selectedDate"
                label="Fecha"
                prepend-inner-icon="mdi-calendar-month-outline"
                type="date"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" md="4">
              <v-select
                v-model="selectedModality"
                :items="modalityOptions"
                item-title="title"
                item-value="value"
                label="Modalidad"
                prepend-inner-icon="mdi-hospital-box-outline"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" md="4">
              <v-textarea
                v-model="patientNote"
                auto-grow
                label="Nota para el profesional"
                prepend-inner-icon="mdi-note-text-outline"
                rows="1"
                variant="outlined"
              />
            </v-col>
          </v-row>

          <div class="d-flex flex-wrap ga-3">
            <v-btn
              :loading="loadingSlots"
              color="primary"
              prepend-icon="mdi-refresh"
              @click="loadSlots"
            >
              Recargar slots
            </v-btn>

            <v-btn
              v-if="bookingSuccess"
              color="success"
              prepend-icon="mdi-calendar-check"
              variant="tonal"
              @click="goToAppointments"
            >
              Ver mis citas
            </v-btn>
          </div>
        </v-card-text>
      </v-card>

      <v-card rounded="xl">
        <v-card-item>
          <v-card-title class="text-h6">Slots disponibles</v-card-title>
          <v-card-subtitle>
            Fecha: {{ selectedDate }} · Modalidad: {{ selectedModality }}
          </v-card-subtitle>
        </v-card-item>

        <v-card-text>
          <v-alert
            v-if="slotsError"
            class="mb-4"
            type="error"
            variant="tonal"
          >
            {{ slotsError }}
          </v-alert>

          <v-skeleton-loader
            v-if="loadingSlots"
            rounded="xl"
            type="list-item-three-line, list-item-three-line, list-item-three-line"
          />

          <v-alert
            v-else-if="!slots.length"
            type="info"
            variant="tonal"
          >
            No existen slots visibles para la fecha y modalidad seleccionadas.
          </v-alert>

          <v-list v-else lines="two">
            <v-list-item
              v-for="slot in slots"
              :key="slot.start"
              :subtitle="`Fin: ${formatSlotDateTime(slot.end)}`"
              :title="formatSlotDateTime(slot.start)"
              class="px-0"
            >
              <template #append>
                <div class="d-flex align-center ga-3">
                  <v-chip
                    :color="slot.is_available ? 'success' : 'grey'"
                    variant="tonal"
                  >
                    {{ slot.is_available ? 'Disponible' : 'No disponible' }}
                  </v-chip>

                  <v-btn
                    :disabled="!slot.is_available || Boolean(bookingInProgressFor)"
                    :loading="bookingInProgressFor === slot.start"
                    color="primary"
                    prepend-icon="mdi-calendar-plus"
                    @click="handleBook(slot)"
                  >
                    Reservar
                  </v-btn>
                </div>
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
    </template>
  </div>
</template>
