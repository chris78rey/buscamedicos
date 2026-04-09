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
