---
name: web-frontend
description: 'Nuxt 4 + Vue 3 + Vuetify frontend for BuscaMedicos. Pages, layouts, components, composables, and stores patterns.'
license: MIT
---

# Web Frontend Skill

## Overview

Nuxt 4 + Vue 3 + Vuetify frontend for BuscaMedicos. Located in `web_frontend/` directory. Consumes FastAPI backend at `http://localhost:8000/api/v1`.

## Project Structure

```
web_frontend/
├── app.vue                      # Root app component
├── nuxt.config.ts              # Nuxt configuration
├── package.json                 # Dependencies (Nuxt 4, Vuetify 4, Pinia, Zod)
├── plugins/
│   └── vuetify.ts              # Vuetify setup
├── middleware/
│   ├── auth.ts                 # Protects routes requiring auth
│   ├── guest.ts                # Redirects authenticated users from login
│   └── role.ts                 # Role-based access control
├── composables/
│   ├── useApi.ts               # API calls with JWT
│   └── useAuth.ts              # Auth helpers (resolveRoleHome, bootstrapAuth)
├── stores/
│   └── auth.ts                 # Pinia auth store
├── layouts/
│   ├── default.vue             # Main app layout
│   ├── auth.vue                # Login/register layout
│   ├── patient.vue             # Patient dashboard layout
│   ├── professional.vue        # Professional dashboard layout
│   └── admin.vue               # Admin dashboard layout
├── pages/
│   ├── index.vue               # Landing page
│   ├── login.vue               # Login form
│   ├── register.vue            # Patient/professional registration
│   ├── patient/
│   ├── professional/
│   ├── admin/
│   └── privacy-auditor/
├── components/
│   ├── app/
│   ├── auth/
│   ├── professional/
│   ├── appointment/
│   ├── privacy/
│   └── moderation/
└── types/
    ├── auth.ts                 # Auth types (CurrentUser, RoleCode)
    ├── user.ts
    ├── professional.ts
    ├── appointment.ts
    └── privacy.ts
```

## Nuxt Config

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  devtools: { enabled: true },
  css: ['vuetify/styles', '@mdi/font/css/materialdesignicons.css'],
  build: { transpile: ['vuetify'] },
  modules: ['@pinia/nuxt'],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1',
    },
  },
  vite: { ssr: { noExternal: ['vuetify'] } },
})
```

## Running

```bash
# Development
cd web_frontend && npm run dev

# Production build
npm run build && npm run preview

# With custom API URL
NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1 npm run dev
```

## Page Pattern

```vue
<script setup lang="ts">
definePageMeta({
  layout: 'patient',           // Use matching layout
  middleware: ['auth', 'role'], // Apply auth + role middleware
  roles: ['patient'],           // Required roles (optional)
})
</script>

<template>
  <!-- Page content with Vuetify components -->
</template>
```

## Vuetify Components

```vue
<v-app>
  <v-app-bar>
    <v-app-bar-title>Title</v-app-bar-title>
  </v-app-bar>
  <v-main>
    <v-container>
      <v-card rounded="xl">
        <v-card-item>
          <v-card-title>Title</v-card-title>
          <v-card-subtitle>Subtitle</v-card-subtitle>
        </v-card-item>
        <v-card-text>Content</v-card-text>
        <v-card-actions>
          <v-btn color="primary">Action</v-btn>
        </v-card-actions>
      </v-card>
    </v-container>
  </v-main>
</v-app>
```

## API Calls

```ts
const { apiFetch } = useApi()

// GET request
const data = await apiFetch<MyType>('/endpoint', { method: 'GET' })

// POST request
const result = await apiFetch<TokenResponse>('/auth/login', {
  method: 'POST',
  body: { email, password },
})
```

## Form Validation with Zod

```vue
<script setup lang="ts">
import { z } from 'zod'

const schema = z.object({
  email: z.email('Email inválido'),
  password: z.string().min(8, 'Mínimo 8 caracteres'),
})

const form = reactive({ email: '', password: '' })

function handleSubmit() {
  const validation = schema.safeParse(form)
  if (!validation.success) {
    formError.value = validation.error.issues[0]?.message
    return
  }
  // Submit validation.data
}
</script>
```

## Role Codes

```ts
type RoleCode =
  | 'super_admin'
  | 'admin_validation'
  | 'admin_support'
  | 'admin_moderation'
  | 'admin_privacy'
  | 'patient'
  | 'professional'
  | 'privacy_auditor'
```

## Gotchas

- Use `$fetch` via `useApi()` composable, not direct fetch
- Token stored in cookie via `useCookie('access_token')`
- Middleware runs on client + server; use `definePageMeta` for page-level config
- Vuetify 4 uses different imports than Vuetify 3
- Admin roles: `super_admin`, `admin_validation`, `admin_support`, `admin_moderation`, `admin_privacy`
