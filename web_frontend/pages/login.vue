<script setup lang="ts">
import { FetchError } from 'ofetch'
import { z } from 'zod'

import type { LoginPayload, TokenResponse } from '~/types/auth'

definePageMeta({
  layout: 'auth',
  middleware: ['guest'],
})

const route = useRoute()
const authStore = useAuthStore()
const { apiFetch } = useApi()
const { resolveRoleHome } = useAuth()

const form = reactive<LoginPayload>({
  email: '',
  password: '',
})

const isSubmitting = ref(false)
const formError = ref('')

const schema = z.object({
  email: z.email('Ingresa un email valido.'),
  password: z.string().min(8, 'La contrasena debe tener al menos 8 caracteres.'),
})

async function handleSubmit() {
  formError.value = ''
  const validation = schema.safeParse(form)

  if (!validation.success) {
    formError.value = validation.error.issues[0]?.message ?? 'Revisa los datos del formulario.'
    return
  }

  isSubmitting.value = true

  try {
    const response = await apiFetch<TokenResponse>('/auth/login', {
      method: 'POST',
      body: validation.data,
    })

    authStore.setToken(response.access_token)
    const user = await authStore.fetchMe()
    const requestedRedirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    const target = requestedRedirect.startsWith('/')
      ? requestedRedirect
      : resolveRoleHome(authStore.roleCodes)

    if (user) {
      await navigateTo(target)
    }
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      formError.value = error.data?.detail?.toString() || 'No se pudo iniciar sesion.'
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
      <v-card-title class="text-h4">Iniciar sesion</v-card-title>
      <v-card-subtitle>Accede segun tu rol dentro de BuscaMedicos.</v-card-subtitle>
    </v-card-item>

    <v-card-text>
      <v-alert v-if="formError" class="mb-4" type="error" variant="tonal">
        {{ formError }}
      </v-alert>

      <v-form @submit.prevent="handleSubmit">
        <v-text-field
          v-model="form.email"
          autocomplete="email"
          label="Email"
          prepend-inner-icon="mdi-email-outline"
          type="email"
          variant="outlined"
        />
        <v-text-field
          v-model="form.password"
          autocomplete="current-password"
          label="Contrasena"
          prepend-inner-icon="mdi-lock-outline"
          type="password"
          variant="outlined"
        />

        <v-btn :loading="isSubmitting" block color="primary" size="large" type="submit">
          Entrar
        </v-btn>
      </v-form>
    </v-card-text>

    <v-card-actions class="px-6 pb-6">
      <span class="text-body-2 text-medium-emphasis">No tienes cuenta?</span>
      <v-spacer />
      <v-btn to="/register" variant="text">Registrarme</v-btn>
    </v-card-actions>
  </v-card>
</template>
