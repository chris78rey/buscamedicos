<script setup lang="ts">
import { FetchError } from 'ofetch'

definePageMeta({
  layout: 'professional',
  middleware: ['auth', 'role'],
  roles: ['professional'],
})

const { getMyPrices, updateMyPrice } = useApi()

type PriceItem = {
  id: string
  modality_code: string
  amount: number
  currency_code: string
  is_active: boolean
}

const prices = ref<PriceItem[]>([])
const loading = ref(false)
const saving = ref<string | null>(null)
const errorMessage = ref('')
const successMessage = ref('')

const modalityOptions = [
  { title: 'Consulta presencial', value: 'in_person_consultorio' },
  { title: 'Teleconsulta', value: 'teleconsulta' },
]

const editingModality = ref('')
const editingAmount = ref<number | null>(null)

const defaultPrices: Record<string, number> = {
  in_person_consultorio: 50,
  teleconsulta: 40,
}

function formatCurrency(value?: number | null, currency = 'USD') {
  if (value === null || value === undefined) return 'N/A'
  return new Intl.NumberFormat('es-EC', {
    style: 'currency',
    currency,
  }).format(value)
}

function getPriceForModality(modality: string) {
  return prices.value.find(p => p.modality_code === modality)
}

function startEditing(modality: string) {
  const existing = getPriceForModality(modality)
  editingModality.value = modality
  editingAmount.value = existing?.amount ?? defaultPrices[modality] ?? 0
}

function cancelEditing() {
  editingModality.value = ''
  editingAmount.value = null
}

async function loadPrices() {
  loading.value = true
  errorMessage.value = ''

  try {
    prices.value = await getMyPrices()
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudieron cargar los precios.'
    }
    else {
      errorMessage.value = 'Error al cargar precios.'
    }
    prices.value = []
  }
  finally {
    loading.value = false
  }
}

async function handleSave(modality: string) {
  if (editingAmount.value === null || editingAmount.value <= 0) {
    errorMessage.value = 'El monto debe ser mayor a 0.'
    return
  }

  saving.value = modality
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const updated = await updateMyPrice(modality, editingAmount.value)
    const existingIndex = prices.value.findIndex(p => p.modality_code === modality)
    if (existingIndex >= 0) {
      prices.value[existingIndex] = updated
    }
    else {
      prices.value.push(updated)
    }
    cancelEditing()
    successMessage.value = 'Precio actualizado correctamente.'
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      errorMessage.value = error.data?.detail?.toString() || 'No se pudo actualizar el precio.'
    }
    else {
      errorMessage.value = 'Error al actualizar el precio.'
    }
  }
  finally {
    saving.value = null
  }
}

onMounted(() => {
  loadPrices()
})
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <div class="d-flex justify-space-between align-center flex-wrap ga-3">
      <div>
        <h2 class="text-h5">Configurar precios</h2>
        <p class="text-body-2 text-medium-emphasis mb-0">
          Establezca el precio para cada modalidad de atencion.
        </p>
      </div>

      <v-btn
        :loading="loading"
        prepend-icon="mdi-refresh"
        variant="outlined"
        @click="loadPrices"
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
        <v-card-title>Precios por modalidad</v-card-title>
        <v-card-subtitle>
          Configure el precio para consultas presenciales y teleconsultas.
        </v-card-subtitle>
      </v-card-item>

      <v-card-text>
        <v-skeleton-loader
          v-if="loading"
          rounded="xl"
          type="list-item-two-line"
        />

        <v-list v-else>
          <v-list-item
            v-for="modality in modalityOptions"
            :key="modality.value"
          >
            <template #prepend>
              <v-icon
                :icon="modality.value === 'in_person_consultorio' ? 'mdi-account-group-outline' : 'mdi-video-outline'"
              />
            </template>

            <v-list-item-title>{{ modality.title }}</v-list-item-title>

            <v-list-item-subtitle>
              <template v-if="editingModality === modality.value">
                <v-text-field
                  v-model.number="editingAmount"
                  :disabled="saving === modality.value"
                  label="Monto (USD)"
                  prepend-inner-icon="mdi-currency-usd"
                  type="number"
                  variant="outlined"
                  density="compact"
                  style="max-width: 200px;"
                />
              </template>
              <template v-else>
                {{ formatCurrency(getPriceForModality(modality.value)?.amount) }}
              </template>
            </v-list-item-subtitle>

            <template #append>
              <template v-if="editingModality === modality.value">
                <v-btn
                  :loading="saving === modality.value"
                  color="success"
                  size="small"
                  variant="tonal"
                  @click="handleSave(modality.value)"
                >
                  Guardar
                </v-btn>
                <v-btn
                  :disabled="saving === modality.value"
                  color="grey"
                  size="small"
                  variant="text"
                  @click="cancelEditing"
                >
                  Cancelar
                </v-btn>
              </template>
              <template v-else>
                <v-btn
                  color="primary"
                  size="small"
                  variant="tonal"
                  @click="startEditing(modality.value)"
                >
                  {{ getPriceForModality(modality.value) ? 'Editar' : 'Crear' }}
                </v-btn>
              </template>
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>

    <v-alert type="info" variant="tonal">
      Los precios aqui configurados seran los que los pacientes veran al reservar una cita con usted.
      La comision de la plataforma se aplicara al momento del pago.
    </v-alert>
  </div>
</template>
