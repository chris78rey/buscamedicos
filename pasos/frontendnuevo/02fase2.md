Se deben reemplazar estos archivos para cerrar la Fase 2 del paciente en Nuxt. Las vistas `patient/professionals.vue`, `patient/professionals/[id].vue` y `patient/appointments.vue` siguen en placeholder, mientras el backend ya expone `GET /public/professionals`, `GET /public/professionals/{identifier}`, `GET /public/professionals/{professional_id}/slots`, `POST /patient/appointments` y `GET /patient/appointments`. El store actual ya soporta bootstrap con `/auth/me` y fallback a `/users/me`, donde se devuelven `role_codes`, `primary_role` y `actor_type`.      

## 1) `web_frontend/types/professional.ts`

```ts
export type ProfessionalSpecialty =
  | string
  | {
      code?: string
      name: string
    }

export type PublicProfessionalListItem = {
  professional_id: string
  public_slug?: string | null
  public_display_name: string
  public_title: string
  specialties: ProfessionalSpecialty[]
  province?: string | null
  city?: string | null
  sector?: string | null
  modalities?: string[]
  years_experience?: number | null
  consultation_price?: number | null
  next_available_at?: string | null
}

export type PublicProfessionalDetail = {
  professional_id: string
  public_display_name: string
  public_title: string
  public_bio?: string | null
  specialties: ProfessionalSpecialty[]
  province?: string | null
  city?: string | null
  sector?: string | null
  years_experience?: number | null
  consultation_price?: number | null
  modalities?: string[]
}

export type SlotItem = {
  start: string
  end: string
  is_available: boolean
}

export type ProfessionalSearchFilters = {
  city?: string
  specialty?: string
  modality?: string
  available_date?: string
}
```

## 2) `web_frontend/types/appointment.ts`

```ts
export type AppointmentCreatePayload = {
  professional_id: string
  modality_code: string
  scheduled_start: string
  patient_note?: string
}

export type AppointmentCreatedResponse = {
  id: string
  public_code: string
  status: string
  scheduled_start: string
  scheduled_end: string
}

export type AppointmentSummary = {
  id: string
  public_code?: string | null
  status: string
  scheduled_start: string
  scheduled_end: string
  modality_code?: string | null
  patient_note?: string | null
  cancellation_reason?: string | null
  reschedule_reason?: string | null
  created_at?: string | null
}
```

## 3) `web_frontend/composables/useApi.ts`

```ts
import type {
  AppointmentCreatePayload,
  AppointmentCreatedResponse,
  AppointmentSummary,
} from '~/types/appointment'
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
    const query = cleanQuery({
      city: filters.city,
      specialty: filters.specialty,
      modality: filters.modality,
      available_date: filters.available_date,
    })

    const queryString = new URLSearchParams(query as Record<string, string>).toString()
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

  return {
    apiFetch,
    searchProfessionals,
    getPublicProfessional,
    getSlots,
    createAppointment,
    getMyAppointments,
  }
}
```

## 4) `web_frontend/pages/patient/professionals.vue`

```vue
<script setup lang="ts">
import { FetchError } from 'ofetch'

import type {
  ProfessionalSearchFilters,
  ProfessionalSpecialty,
  PublicProfessionalListItem,
} from '~/types/professional'

definePageMeta({
  layout: 'patient',
  middleware: ['auth', 'role'],
  roles: ['patient'],
})

const { searchProfessionals } = useApi()

const filters = reactive<ProfessionalSearchFilters>({
  city: '',
  specialty: '',
  modality: '',
  available_date: '',
})

const professionals = ref<PublicProfessionalListItem[]>([])
const loading = ref(false)
const searchedOnce = ref(false)
const errorMessage = ref('')

const modalityOptions = [
  { title: 'Todas', value: '' },
  { title: 'Consulta presencial', value: 'in_person_consultorio' },
  { title: 'Teleconsulta', value: 'teleconsulta' },
]

function professionalIdentifier(item: PublicProfessionalListItem) {
  return item.public_slug || item.professional_id
}

function specialtyLabel(item: ProfessionalSpecialty) {
  return typeof item === 'string' ? item : item.name
}

function formatSpecialties(items: ProfessionalSpecialty[] | undefined) {
  if (!items?.length) {
    return 'Sin especialidad visible'
  }

  return items.map(specialtyLabel).join(', ')
}

function formatLocation(item: PublicProfessionalListItem) {
  return [item.city, item.province].filter(Boolean).join(', ') || 'Ubicacion no disponible'
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

function formatNextAvailability(value?: string | null) {
  if (!value) {
    return 'Sin disponibilidad proxima reportada'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString('es-EC', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

async function runSearch() {
  loading.value = true
  errorMessage.value = ''

  try {
    professionals.value = await searchProfessionals(filters)
    searchedOnce.value = true
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo consultar la lista de profesionales.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado al consultar profesionales.'
    }
    professionals.value = []
  }
  finally {
    loading.value = false
  }
}

function clearFilters() {
  filters.city = ''
  filters.specialty = ''
  filters.modality = ''
  filters.available_date = ''
  runSearch()
}

onMounted(() => {
  runSearch()
})
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <v-card rounded="xl">
      <v-card-item>
        <v-card-title class="text-h5">Busqueda de profesionales</v-card-title>
        <v-card-subtitle>
          Se permite filtrar por ciudad, especialidad, modalidad y fecha disponible.
        </v-card-subtitle>
      </v-card-item>

      <v-card-text>
        <v-alert
          v-if="errorMessage"
          class="mb-4"
          type="error"
          variant="tonal"
        >
          {{ errorMessage }}
        </v-alert>

        <v-row>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.city"
              clearable
              label="Ciudad"
              prepend-inner-icon="mdi-map-marker-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.specialty"
              clearable
              label="Especialidad"
              prepend-inner-icon="mdi-stethoscope"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-select
              v-model="filters.modality"
              :items="modalityOptions"
              item-title="title"
              item-value="value"
              label="Modalidad"
              prepend-inner-icon="mdi-hospital-box-outline"
              variant="outlined"
            />
          </v-col>

          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.available_date"
              label="Fecha disponible"
              prepend-inner-icon="mdi-calendar-month-outline"
              type="date"
              variant="outlined"
            />
          </v-col>
        </v-row>

        <div class="d-flex flex-wrap ga-3">
          <v-btn
            :loading="loading"
            color="primary"
            prepend-icon="mdi-magnify"
            @click="runSearch"
          >
            Buscar
          </v-btn>

          <v-btn
            color="default"
            prepend-icon="mdi-filter-off-outline"
            variant="tonal"
            @click="clearFilters"
          >
            Limpiar filtros
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <div class="d-flex justify-space-between align-center">
      <div>
        <div class="text-h6">Resultados</div>
        <div class="text-body-2 text-medium-emphasis">
          {{ professionals.length }} profesional(es) encontrado(s)
        </div>
      </div>
    </div>

    <v-row v-if="loading">
      <v-col
        v-for="n in 3"
        :key="n"
        cols="12"
        md="4"
      >
        <v-skeleton-loader
          rounded="xl"
          type="article, actions"
        />
      </v-col>
    </v-row>

    <v-alert
      v-else-if="searchedOnce && !professionals.length"
      type="info"
      variant="tonal"
    >
      No existen resultados con los filtros actuales.
    </v-alert>

    <v-row v-else>
      <v-col
        v-for="item in professionals"
        :key="item.professional_id"
        cols="12"
        md="6"
        lg="4"
      >
        <v-card class="h-100" rounded="xl">
          <v-card-item prepend-icon="mdi-account-heart-outline">
            <v-card-title>{{ item.public_display_name }}</v-card-title>
            <v-card-subtitle>{{ item.public_title }}</v-card-subtitle>
          </v-card-item>

          <v-card-text class="d-flex flex-column ga-3">
            <div>
              <div class="text-caption text-medium-emphasis">Especialidades</div>
              <div class="text-body-2">{{ formatSpecialties(item.specialties) }}</div>
            </div>

            <div>
              <div class="text-caption text-medium-emphasis">Ubicacion</div>
              <div class="text-body-2">{{ formatLocation(item) }}</div>
            </div>

            <div>
              <div class="text-caption text-medium-emphasis">Experiencia</div>
              <div class="text-body-2">
                {{ item.years_experience ?? 'No reportada' }}
              </div>
            </div>

            <div>
              <div class="text-caption text-medium-emphasis">Precio referencial</div>
              <div class="text-body-2">{{ formatCurrency(item.consultation_price) }}</div>
            </div>

            <div>
              <div class="text-caption text-medium-emphasis">Proxima disponibilidad</div>
              <div class="text-body-2">{{ formatNextAvailability(item.next_available_at) }}</div>
            </div>
          </v-card-text>

          <v-card-actions>
            <v-btn
              :to="`/patient/professionals/${professionalIdentifier(item)}`"
              color="primary"
              prepend-icon="mdi-calendar-plus"
              variant="tonal"
            >
              Ver detalle y reservar
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
```

## 5) `web_frontend/pages/patient/professionals/[id].vue`

```vue
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
```

## 6) `web_frontend/pages/patient/appointments.vue`

```vue
<script setup lang="ts">
import { FetchError } from 'ofetch'

import type { AppointmentSummary } from '~/types/appointment'

definePageMeta({
  layout: 'patient',
  middleware: ['auth', 'role'],
  roles: ['patient'],
})

const { getMyAppointments } = useApi()

const appointments = ref<AppointmentSummary[]>([])
const loading = ref(false)
const errorMessage = ref('')

const statusMeta: Record<string, { label: string; color: string }> = {
  pending_confirmation: {
    label: 'Pendiente de confirmacion',
    color: 'warning',
  },
  confirmed: {
    label: 'Confirmada',
    color: 'primary',
  },
  completed: {
    label: 'Completada',
    color: 'success',
  },
  cancelled_by_patient: {
    label: 'Cancelada por paciente',
    color: 'error',
  },
  cancelled_by_professional: {
    label: 'Cancelada por profesional',
    color: 'error',
  },
  no_show_patient: {
    label: 'Paciente no asistio',
    color: 'deep-orange',
  },
  no_show_professional: {
    label: 'Profesional no asistio',
    color: 'deep-orange',
  },
}

function resolveStatus(status: string) {
  return statusMeta[status] ?? {
    label: status,
    color: 'grey',
  }
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return 'Sin fecha'
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

function formatModality(value?: string | null) {
  if (!value) {
    return 'Modalidad no disponible'
  }

  const labels: Record<string, string> = {
    in_person_consultorio: 'Consulta presencial',
    teleconsulta: 'Teleconsulta',
  }

  return labels[value] ?? value
}

async function loadAppointments() {
  loading.value = true
  errorMessage.value = ''

  try {
    appointments.value = await getMyAppointments()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudieron consultar las citas.'
    }
    else {
      errorMessage.value = 'Ocurrio un error inesperado al cargar las citas.'
    }

    appointments.value = []
  }
  finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAppointments()
})
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <div class="d-flex justify-space-between align-center flex-wrap ga-3">
      <div>
        <h2 class="text-h5">Mis citas</h2>
        <p class="text-body-2 text-medium-emphasis mb-0">
          Se listan las citas del paciente en orden descendente por fecha.
        </p>
      </div>

      <div class="d-flex flex-wrap ga-3">
        <v-btn
          color="primary"
          prepend-icon="mdi-magnify"
          variant="tonal"
          @click="$router.push('/patient/professionals')"
        >
          Buscar profesionales
        </v-btn>

        <v-btn
          :loading="loading"
          prepend-icon="mdi-refresh"
          variant="outlined"
          @click="loadAppointments"
        >
          Recargar
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

    <v-skeleton-loader
      v-else-if="loading"
      rounded="xl"
      type="article, article, article"
    />

    <v-alert
      v-else-if="!appointments.length"
      type="info"
      variant="tonal"
    >
      El paciente todavia no registra citas. Se puede ir a la busqueda de profesionales para crear la primera.
    </v-alert>

    <v-row v-else>
      <v-col
        v-for="appointment in appointments"
        :key="appointment.id"
        cols="12"
        md="6"
      >
        <v-card class="h-100" rounded="xl">
          <v-card-item>
            <template #append>
              <v-chip
                :color="resolveStatus(appointment.status).color"
                variant="tonal"
              >
                {{ resolveStatus(appointment.status).label }}
              </v-chip>
            </template>

            <v-card-title>
              {{ appointment.public_code || `Cita ${appointment.id.slice(0, 8)}` }}
            </v-card-title>

            <v-card-subtitle>
              {{ formatModality(appointment.modality_code) }}
            </v-card-subtitle>
          </v-card-item>

          <v-card-text class="d-flex flex-column ga-3">
            <div>
              <div class="text-caption text-medium-emphasis">Inicio</div>
              <div class="text-body-2">{{ formatDateTime(appointment.scheduled_start) }}</div>
            </div>

            <div>
              <div class="text-caption text-medium-emphasis">Fin</div>
              <div class="text-body-2">{{ formatDateTime(appointment.scheduled_end) }}</div>
            </div>

            <div v-if="appointment.patient_note">
              <div class="text-caption text-medium-emphasis">Nota del paciente</div>
              <div class="text-body-2" style="white-space: pre-line;">
                {{ appointment.patient_note }}
              </div>
            </div>

            <div v-if="appointment.cancellation_reason">
              <div class="text-caption text-medium-emphasis">Motivo de cancelacion</div>
              <div class="text-body-2">{{ appointment.cancellation_reason }}</div>
            </div>

            <div v-if="appointment.reschedule_reason">
              <div class="text-caption text-medium-emphasis">Motivo de reagendamiento</div>
              <div class="text-body-2">{{ appointment.reschedule_reason }}</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
```

## 7) Instrucción corta para el desarrollador

Se deben reemplazar exactamente esos 6 archivos.
No se debe tocar backend, store de auth, middleware ni layouts.
Después solo se debe levantar:

```bash
cd web_frontend
npm install
NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1 npm run dev
```

El repomix actualizado del repositorio está aquí: [repomix-output.xml](sandbox:/mnt/data/repomix-output.xml)
