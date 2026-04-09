---
name: frontend-auth
description: 'Authentication patterns for BuscaMedicos web frontend. JWT handling, login, register, session persistence, and role-based redirection.'
license: MIT
---

# Frontend Auth Skill

## Overview

JWT-based authentication for the BuscaMedicos Nuxt frontend. Auth state managed via Pinia store with cookie persistence.

## Auth Store (`stores/auth.ts`)

```ts
import { defineStore } from 'pinia'

type CurrentUser = {
  id: string
  email: string
  status?: string
  is_email_verified?: boolean
  role_codes?: RoleCode[]
  primary_role?: RoleCode | null
  actor_type?: 'admin' | 'patient' | 'professional' | 'unknown'
  roles?: UserRole[]
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: null,
    user: null,
    loaded: false,
  }),
  getters: {
    roleCodes: (state): RoleCode[] => getRoleCodes(state.user),
    isAuthenticated: (state): boolean => Boolean(state.token),
  },
  actions: {
    hydrateFromCookie() { /* Restore token from cookie */ },
    setToken(token: string | null) { /* Set token + cookie */ },
    async fetchMe() { /* GET /auth/me */ },
    async bootstrap() { /* Hydrate + fetch user */ },
    logout() { /* Clear state + cookie */ },
  },
})
```

## Auth Composable (`composables/useAuth.ts`)

```ts
export function useAuth() {
  function resolveRoleHome(roles: RoleCode[]): string {
    if (roles.includes('privacy_auditor')) return '/privacy-auditor/access-logs'
    if (roles.some(isAdminRole)) return '/admin/dashboard'
    if (roles.includes('professional')) return '/professional/dashboard'
    return '/patient/dashboard'
  }

  async function bootstrapAuth() {
    const authStore = useAuthStore()
    if (!authStore.loaded) {
      await authStore.bootstrap()
    }
    return authStore
  }

  return { resolveRoleHome, bootstrapAuth, getRoleCodes, isAdminRole }
}
```

## API Composable (`composables/useApi.ts`)

```ts
export function useApi() {
  const config = useRuntimeConfig()
  const token = useCookie<string | null>('access_token')

  async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
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

  return { apiFetch }
}
```

## Middleware

### auth.ts - Protects routes
```ts
export default defineNuxtRouteMiddleware(async (to) => {
  const { bootstrapAuth } = useAuth()
  const authStore = await bootstrapAuth()

  if (!authStore.isAuthenticated || !authStore.user) {
    return navigateTo(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }
})
```

### guest.ts - Redirects authenticated users
```ts
export default defineNuxtRouteMiddleware(async () => {
  const { bootstrapAuth, resolveRoleHome } = useAuth()
  const authStore = await bootstrapAuth()

  if (authStore.isAuthenticated && authStore.user) {
    return navigateTo(resolveRoleHome(authStore.roleCodes))
  }
})
```

### role.ts - Role-based access
```ts
export default defineNuxtRouteMiddleware(async (to) => {
  const expectedRoles = (to.meta.roles ?? []) as RoleCode[]
  if (!expectedRoles.length) return

  const { bootstrapAuth, resolveRoleHome } = useAuth()
  const authStore = await bootstrapAuth()

  if (!authStore.isAuthenticated || !authStore.user) {
    return navigateTo(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }

  if (expectedRoles.some(role => authStore.roleCodes.includes(role))) {
    return
  }

  return navigateTo(resolveRoleHome(authStore.roleCodes))
})
```

## Login Page Pattern

```vue
<script setup lang="ts">
import { FetchError } from 'ofetch'
import { z } from 'zod'

definePageMeta({ layout: 'auth', middleware: ['guest'] })

const form = reactive({ email: '', password: '' })
const isSubmitting = ref(false)
const formError = ref('')

const schema = z.object({
  email: z.email('Email inválido'),
  password: z.string().min(8, 'Mínimo 8 caracteres'),
})

async function handleSubmit() {
  formError.value = ''
  const validation = schema.safeParse(form)
  if (!validation.success) {
    formError.value = validation.error.issues[0]?.message
    return
  }

  isSubmitting.value = true
  try {
    const { apiFetch } = useApi()
    const authStore = useAuthStore()
    const { resolveRoleHome } = useAuth()

    const response = await apiFetch<TokenResponse>('/auth/login', {
      method: 'POST',
      body: validation.data,
    })

    authStore.setToken(response.access_token)
    const user = await authStore.fetchMe()
    if (user) {
      await navigateTo(resolveRoleHome(authStore.roleCodes))
    }
  }
  catch (error: unknown) {
    if (error instanceof FetchError) {
      formError.value = error.data?.detail?.toString() || 'Error de login'
    }
  }
  finally {
    isSubmitting.value = false
  }
}
</script>
```

## Register Page Pattern

```vue
<script setup lang="ts">
const accountRole = ref<'patient' | 'professional'>('patient')
const form = reactive({ first_name: '', last_name: '', email: '', password: '', national_id: '', phone: '' })

async function handleSubmit() {
  const endpoint = accountRole.value === 'patient'
    ? '/auth/register/patient'
    : '/auth/register/professional'

  const payload = accountRole.value === 'patient'
    ? validation.data
    : { ...validation.data, professional_type: 'general' }

  const response = await apiFetch<TokenResponse>(endpoint, {
    method: 'POST',
    body: payload,
  })

  authStore.setToken(response.access_token)
  await authStore.fetchMe()
  await navigateTo(resolveRoleHome(authStore.roleCodes))
}
</script>
```

## Role Redirection

| Role | Redirects to |
|------|-------------|
| `patient` | `/patient/dashboard` |
| `professional` | `/professional/dashboard` |
| `super_admin`, `admin_*` | `/admin/dashboard` |
| `privacy_auditor` | `/privacy-auditor/access-logs` |

## API Endpoints Used

| Method | Endpoint | Usage |
|--------|----------|-------|
| POST | `/auth/login` | Login |
| POST | `/auth/register/patient` | Patient registration |
| POST | `/auth/register/professional` | Professional registration |
| GET | `/auth/me` | Get current user |

## Gotchas

- Always use `authStore.setToken()` which also updates the cookie
- Call `authStore.bootstrap()` on app load to restore session
- Use `definePageMeta({ middleware: ['auth'] })` on protected pages
- Guest pages (login/register) should use `middleware: ['guest']`
- Handle `FetchError` for proper error messages from API
- Token stored as `access_token` cookie, not in localStorage
