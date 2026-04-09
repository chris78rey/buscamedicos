<script setup lang="ts">
import { FetchError } from 'ofetch'
import { z } from 'zod'

import type { RegisterPayload, RegisterRole, TokenResponse } from '~/types/auth'

definePageMeta({
  layout: 'auth',
  middleware: ['guest'],
})

const authStore = useAuthStore()
const { apiFetch } = useApi()
const { resolveRoleHome } = useAuth()

const accountRole = ref<RegisterRole>('patient')
const form = reactive<RegisterPayload>({
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  national_id: '',
  phone: '',
})

const isSubmitting = ref(false)
const formError = ref('')

const schema = z.object({
  first_name: z.string().min(2, 'Ingresa los nombres.'),
  last_name: z.string().min(2, 'Ingresa los apellidos.'),
  email: z.email('Ingresa un email valido.'),
  password: z.string().min(8, 'La contrasena debe tener al menos 8 caracteres.'),
  national_id: z.string().min(10, 'La cedula debe tener al menos 10 caracteres.'),
  phone: z.string().min(7, 'Ingresa un telefono valido.'),
})

async function handleSubmit() {
  formError.value = ''
  const validation = schema.safeParse(form)

  if (!validation.success) {
    formError.value = validation.error.issues[0]?.message ?? 'Revisa los datos del formulario.'
    return
  }

  const endpoint = accountRole.value === 'patient'
    ? '/auth/register/patient'
    : '/auth/register/professional'

  const payload = accountRole.value === 'patient'
    ? validation.data
    : { ...validation.data, professional_type: 'general' }

  isSubmitting.value = true

  try {
    const response = await apiFetch<TokenResponse>(endpoint, {
      method: 'POST',
      body: payload,
    })

    authStore.setToken(response.access_token)
    await authStore.fetchMe()
    await navigateTo(resolveRoleHome(authStore.roleCodes))
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      formError.value = error.data?.detail?.toString() || 'No se pudo completar el registro.'
    }
    else {
      formError.value = 'Ocurrio un error inesperado.'
    }
  }
  finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <v-card rounded="xl">
    <v-card-item class="pb-0">
      <v-card-title class="text-h4">Crear cuenta</v-card-title>
      <v-card-subtitle>Registro inicial para paciente o profesional.</v-card-subtitle>
    </v-card-item>

    <v-card-text>
      <v-alert v-if="formError" class="mb-4" type="error" variant="tonal">
        {{ formError }}
      </v-alert>

      <v-switch
        v-model="accountRole"
        class="mb-4"
        color="primary"
        false-value="patient"
        inset
        label="Crear cuenta profesional"
        true-value="professional"
      />

      <v-form @submit.prevent="handleSubmit">
        <v-row>
          <v-col cols="12" md="6">
            <v-text-field v-model="form.first_name" label="Nombres" variant="outlined" />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field v-model="form.last_name" label="Apellidos" variant="outlined" />
          </v-col>
          <v-col cols="12">
            <v-text-field v-model="form.email" label="Email" type="email" variant="outlined" />
          </v-col>
          <v-col cols="12">
            <v-text-field v-model="form.password" label="Contrasena" type="password" variant="outlined" />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field v-model="form.national_id" label="Cedula" variant="outlined" />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field v-model="form.phone" label="Telefono" variant="outlined" />
          </v-col>
        </v-row>

        <v-btn :loading="isSubmitting" block color="primary" size="large" type="submit">
          {{ accountRole === 'patient' ? 'Registrar paciente' : 'Registrar profesional' }}
        </v-btn>
      </v-form>
    </v-card-text>

    <v-card-actions class="px-6 pb-6">
      <span class="text-body-2 text-medium-emphasis">Ya tienes cuenta?</span>
      <v-spacer />
      <v-btn to="/login" variant="text">Ir a login</v-btn>
    </v-card-actions>
  </v-card>
</template>
