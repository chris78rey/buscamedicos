Sí. Se le puede pasar al programador así, ya masticado, para **migrar la capa web a Nuxt 4 + Vue 3 + Vuetify** sin tocar el backend ni romper el avance ya existente.

El criterio base debe ser este: el proyecto **ya tiene backend FastAPI, migraciones secuenciales, routers por dominio, tests y docker**, y la app actual Flutter ya cubre login, registro, home básico y algunas vistas de búsqueda/clínica; por tanto, **no se debe rehacer el dominio ni el backend**, solo se debe reemplazar la capa web.  

Además, el frontend actual ya consume endpoints reales de auth como `/auth/login`, `/auth/register/patient`, `/auth/register/professional` y `/auth/me`, y ya existen pantallas base para login, registro y home. También ya hay una búsqueda básica de profesionales y varias pantallas de privacidad y moderación siguen siendo placeholders, lo que hace razonable migrar la web ahora sin perder demasiado trabajo visual consolidado.   

A continuación se deja el instructivo.

---

# Instructivo para migrar frontend web a Nuxt 4 + Vue 3 + Vuetify

## 1. Objetivo exacto

Se debe reemplazar `app_flutter` como frontend web principal por una nueva carpeta `web_frontend/` usando:

* Nuxt 4
* Vue 3
* Vuetify
* Pinia
* TypeScript

El backend `backend_api/` se mantiene como está.
No se deben cambiar modelos, migraciones, tablas, reglas de negocio, auditoría ni endpoints, salvo que aparezca un bug puntual de integración. El backend ya está organizado como monolito FastAPI con routers por dominio y entrypoint único en `backend_api/app/main.py`. 

## 2. Regla principal de arquitectura

Se debe aplicar esta regla sin excepción:

**Nuxt será solo la capa web.**
**FastAPI seguirá siendo la única fuente de verdad del negocio.**

Eso significa:

* no mover lógica de negocio a Nuxt
* no duplicar validaciones críticas en frontend
* no crear base de datos desde Nuxt
* no crear backend alterno dentro de Nuxt para reemplazar FastAPI
* no rehacer auth del lado servidor en Node

Nuxt solo debe:

* mostrar pantallas
* manejar sesión web
* consumir APIs existentes
* controlar navegación por rol
* presentar formularios, tablas, filtros y dashboards

## 3. Qué sí se debe conservar del proyecto actual

Se debe conservar intacto:

* `backend_api/`
* `infra/`
* `docs/`
* `tests/`
* `alembic/`
* `scripts/seed.py`

La carpeta `app_flutter/` no se debe borrar todavía.
Se debe dejar como referencia temporal hasta terminar la migración.

## 4. Nueva estructura que se debe crear

Se debe crear esta carpeta nueva en la raíz del repo:

```text
web_frontend/
```

Y dentro:

```text
web_frontend/
  app.vue
  nuxt.config.ts
  package.json
  tsconfig.json
  plugins/
    vuetify.ts
  middleware/
    auth.ts
    guest.ts
    role.ts
  composables/
    useApi.ts
    useAuth.ts
  stores/
    auth.ts
  layouts/
    default.vue
    auth.vue
    admin.vue
    patient.vue
    professional.vue
  pages/
    login.vue
    register.vue
    index.vue
    patient/
      dashboard.vue
      professionals.vue
      professionals/[id].vue
      appointments.vue
      privacy/
        consents.vue
        access-logs.vue
    professional/
      dashboard.vue
      appointments.vue
      teleconsultation/[appointmentId].vue
      privacy/
        access-logs.vue
        exceptional-access.vue
    admin/
      dashboard.vue
      privacy/
        access-logs.vue
        policies.vue
        incidents.vue
      moderation/
        cases.vue
        sanctions.vue
      payments/
        settlements.vue
    privacy-auditor/
      access-logs.vue
  components/
    app/
    auth/
    professional/
    appointment/
    privacy/
    moderation/
  types/
    auth.ts
    user.ts
    professional.ts
    appointment.ts
    privacy.ts
  assets/
  public/
```

## 5. Decisión de migración

No se debe migrar todo de golpe.

Se debe migrar en este orden:

### Fase 1

* login
* register
* bootstrap de sesión
* logout
* `/auth/me`
* redirección por rol

### Fase 2

* búsqueda de profesionales
* detalle del profesional
* listado de slots
* reserva de cita
* citas del paciente

### Fase 3

* pagos básicos si ya están operativos del lado backend
* dashboard por rol

### Fase 4

* privacidad
* acceso excepcional
* auditoría de accesos
* pantallas administrativas

### Fase 5

* moderación
* refinamiento visual
* integración en Docker

No se debe empezar por privacidad o moderación antes de que auth y booking estén estables.

## 6. Qué endpoints se deben reutilizar primero

Del frontend actual ya consta que auth consume:

* `POST /api/v1/auth/login`
* `POST /api/v1/auth/register/patient`
* `POST /api/v1/auth/register/professional`
* `GET /api/v1/auth/me`

Eso ya existe y no se debe reescribir. 

También ya hay consumo frontend de búsqueda de profesionales, detalle, slots y reserva, por lo que el nuevo frontend debe replicar esos flujos usando el mismo backend, no inventar uno nuevo. 

## 7. Instrucción exacta para el programador

Se le puede pasar así:

> Se debe crear una nueva app web en `web_frontend/` con Nuxt 4 + Vue 3 + Vuetify + Pinia + TypeScript. No se debe tocar el backend como fuente principal de negocio. La app Flutter actual queda solo como referencia temporal. Se debe migrar primero auth y booking, luego privacidad y paneles administrativos. El backend ya existe, ya tiene routers por dominio, ya expone auth y ya tiene pruebas y migraciones. La nueva app debe consumir `http://localhost:8000/api/v1` por variable de entorno y manejar JWT en storage seguro para web. No se debe duplicar lógica de negocio en Nuxt.

## 8. Comandos iniciales que debe ejecutar

```bash
cd <raiz-del-repo>
npx nuxi@latest init web_frontend
cd web_frontend
npm install
npm install vuetify vite-plugin-vuetify pinia @pinia/nuxt
npm install @mdi/font sass
npm install zod
```

## 9. Archivo `package.json` esperado

Se debe usar scripts simples:

```json
{
  "scripts": {
    "dev": "nuxt dev",
    "build": "nuxt build",
    "preview": "nuxt preview"
  }
}
```

## 10. Archivo `nuxt.config.ts`

Se debe dejar una base así:

```ts
export default defineNuxtConfig({
  devtools: { enabled: true },
  css: [
    'vuetify/styles',
    '@mdi/font/css/materialdesignicons.css'
  ],
  build: {
    transpile: ['vuetify']
  },
  modules: ['@pinia/nuxt'],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1'
    }
  },
  vite: {
    ssr: {
      noExternal: ['vuetify']
    }
  }
})
```

## 11. Plugin de Vuetify

Crear `plugins/vuetify.ts`:

```ts
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

export default defineNuxtPlugin((nuxtApp) => {
  const vuetify = createVuetify({
    components,
    directives
  })

  nuxtApp.vueApp.use(vuetify)
})
```

## 12. Composable base para API

Crear `composables/useApi.ts`:

```ts
export function useApi() {
  const config = useRuntimeConfig()
  const token = useCookie<string | null>('access_token')

  async function apiFetch<T>(path: string, options: any = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }

    if (token.value) {
      headers.Authorization = `Bearer ${token.value}`
    }

    return await $fetch<T>(`${config.public.apiBase}${path}`, {
      ...options,
      headers
    })
  }

  return { apiFetch }
}
```

## 13. Store de autenticación

Crear `stores/auth.ts`:

```ts
import { defineStore } from 'pinia'

type CurrentUser = {
  id: string
  email: string
  status?: string
  roles?: Array<{ code: string }>
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null as string | null,
    user: null as CurrentUser | null,
    loaded: false
  }),
  actions: {
    setToken(token: string | null) {
      this.token = token
      const cookie = useCookie<string | null>('access_token')
      cookie.value = token
    },
    async fetchMe() {
      const { apiFetch } = useApi()
      this.user = await apiFetch<CurrentUser>('/auth/me', { method: 'GET' })
      this.loaded = true
      return this.user
    },
    logout() {
      this.user = null
      this.setToken(null)
      this.loaded = true
    }
  }
})
```

## 14. Middleware que debe existir

### `middleware/auth.ts`

Debe bloquear acceso si no existe token.

### `middleware/guest.ts`

Debe impedir que un usuario autenticado vuelva a `/login`.

### `middleware/role.ts`

Debe validar rol esperado por página.

No se debe hardcodear lógica desordenada en cada vista.

## 15. Primera pantalla que se debe dejar operativa

### `pages/login.vue`

Debe:

* mostrar email y password
* llamar a `/auth/login`
* guardar `access_token`
* cargar `/auth/me`
* redirigir por rol

Roles esperados en el sistema:

* `super_admin`
* `admin_validation`
* `admin_support`
* `patient`
* `professional` 

La redirección sugerida sería:

* `patient` → `/patient/dashboard`
* `professional` → `/professional/dashboard`
* `super_admin` y admins → `/admin/dashboard`
* `privacy_auditor` → `/privacy-auditor/access-logs`

## 16. Pantalla de registro

### `pages/register.vue`

Debe replicar el flujo actual:

* nombres
* apellidos
* email
* password
* cédula
* teléfono
* switch para paciente o profesional

Si es paciente:

* llamar a `/auth/register/patient`

Si es profesional:

* llamar a `/auth/register/professional`

Después:

* guardar token
* cargar `/auth/me`
* redirigir

Eso ya estaba planteado en la app Flutter y no se debe reinventar. 

## 17. Dashboard base por rol

No se debe empezar con dashboards complejos.

Se deben dejar tres pantallas simples:

### `/patient/dashboard`

Con accesos a:

* buscar profesionales
* mis citas
* privacidad

### `/professional/dashboard`

Con accesos a:

* citas
* teleconsulta
* privacidad
* acceso excepcional

### `/admin/dashboard`

Con accesos a:

* privacidad
* moderación
* pagos
* operaciones

## 18. Migración de búsqueda y reserva

La pantalla Flutter actual ya sugiere este flujo:

* listado de profesionales
* detalle público
* slots disponibles
* reserva de cita 

Por tanto en Nuxt se debe construir:

### `/patient/professionals.vue`

* filtros por ciudad
* filtros por especialidad
* listado de cards

### `/patient/professionals/[id].vue`

* datos públicos
* precio
* slots disponibles
* botón reservar

### `/patient/appointments.vue`

* lista de citas del paciente

No se debe mezclar esta parte con privacidad todavía.

## 19. Migración de privacidad y moderación

Como varias pantallas Flutter de privacidad y moderación todavía son placeholders, Nuxt debe aprovechar eso y hacerlas bien desde cero en web. 

Se debe construir después de auth y booking:

* `/patient/privacy/consents`
* `/patient/privacy/access-logs`
* `/professional/privacy/access-logs`
* `/professional/privacy/exceptional-access`
* `/admin/privacy/access-logs`
* `/admin/privacy/policies`
* `/admin/privacy/incidents`
* `/privacy-auditor/access-logs`

Importante: el backend ya tiene router de `privacy_auditor` y exportación de logs de acceso; por eso Nuxt debe consumir eso, no simularlo. 

## 20. Qué no debe hacer el programador

No se debe:

* borrar `app_flutter`
* tocar `backend_api/app/main.py` sin necesidad
* mover lógica clínica a Nuxt
* rehacer JWT del backend
* inventar una API Node intermedia
* mezclar componentes viejos Flutter con Nuxt
* abrir microfrontends
* crear dos fuentes de verdad para auth
* rehacer migraciones de base

## 21. Criterios de aceptación de la migración mínima

La migración web mínima se debe considerar aceptada cuando cumpla esto:

1. `backend_api` sigue levantando sin cambios funcionales.
2. `web_frontend` levanta con `npm run dev`.
3. login funciona con `/auth/login`.
4. registro funciona con `/auth/register/patient` y `/auth/register/professional`.
5. la sesión persiste en navegador.
6. el usuario autenticado carga `/auth/me`.
7. existe redirección por rol.
8. funciona búsqueda de profesionales.
9. funciona detalle y reserva de cita.
10. `app_flutter` queda intacta como respaldo temporal.

## 22. Comandos para correr local

Backend:

```bash
cd backend_api
uvicorn app.main:app --reload
```

O por Docker desde `infra/`, según el flujo ya documentado en el repo. 

Frontend Nuxt:

```bash
cd web_frontend
npm run dev
```

Con variable:

```bash
NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1 npm run dev
```

## 23. Texto corto listo para pegarle al programador

Se debe crear una nueva app web en `web_frontend/` con Nuxt 4 + Vue 3 + Vuetify + Pinia + TypeScript. No se debe tocar el backend como capa principal de negocio. Se debe conservar `backend_api`, `infra`, migraciones, tests y docs. `app_flutter` queda temporalmente como referencia y no se borra. La nueva app debe consumir `http://localhost:8000/api/v1` por variable de entorno. Primero se deben migrar login, registro, `/auth/me`, persistencia de sesión y redirección por rol. Luego búsqueda de profesionales, detalle, slots y reserva. Después privacidad, auditoría y paneles administrativos. No se debe duplicar lógica de negocio en Nuxt ni crear un backend alterno en Node.

Si se desea, en el siguiente mensaje se puede dejar ya **el prompt exacto para que Codex o el programador cree la carpeta `web_frontend/` con la base de Nuxt 4 + Vuetify**, archivo por archivo.
