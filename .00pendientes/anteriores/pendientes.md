Sí. Según el repomix, lo más seguro y coherente para hoy es cerrar los **4 placeholders restantes del frontend Nuxt** antes de abrir una fase nueva. El propio repo marca que todavía siguen pendientes `professional/appointments.vue`, `admin/moderation/cases.vue`, `admin/moderation/sanctions.vue` y `admin/payments/settlements.vue`, y además indica que en este bloque **no se debe tocar backend, migraciones, composables, store, middleware ni layouts**. Después de eso, el siguiente bloque real ya sería **paso 9 de IA segura y útil**, como fase separada.   

## 1) Impacto y riesgos

**Qué se va a tocar**

* Solo 4 archivos de páginas del frontend.
* Sin cambio de contratos API.
* Sin cambio de base de datos.
* Sin riesgo de romper login, auth, privacidad, búsqueda de profesionales ni flujo de citas del paciente si se respeta el alcance. 

**Riesgo principal**

* Que el programador “aproveche” y toque `useApi.ts`, middleware o layouts.
* Que cambie rutas o roles y rompa navegación.

**Protección**

* Limitarse exactamente a estos 4 archivos:

  * `web_frontend/pages/professional/appointments.vue`
  * `web_frontend/pages/admin/moderation/cases.vue`
  * `web_frontend/pages/admin/moderation/sanctions.vue`
  * `web_frontend/pages/admin/payments/settlements.vue` 

---

## 2) Preparación

### Backup obligatorio

```bash
cd web_frontend

mkdir -p ../backup_frontend_$(date +%Y%m%d_%H%M%S)/pages/professional
mkdir -p ../backup_frontend_$(date +%Y%m%d_%H%M%S)/pages/admin/moderation
mkdir -p ../backup_frontend_$(date +%Y%m%d_%H%M%S)/pages/admin/payments
```

### Backup simple con Git

```bash
git status
git add .
git commit -m "backup antes de cerrar placeholders frontend pendientes"
```

### Backup directo de archivos

```bash
cp web_frontend/pages/professional/appointments.vue /tmp/appointments.vue.bak
cp web_frontend/pages/admin/moderation/cases.vue /tmp/cases.vue.bak
cp web_frontend/pages/admin/moderation/sanctions.vue /tmp/sanctions.vue.bak
cp web_frontend/pages/admin/payments/settlements.vue /tmp/settlements.vue.bak
```

---

## 3) Implementación paso a paso

### Archivo 1: `web_frontend/pages/professional/appointments.vue`

```vue
<script setup lang="ts">
definePageMeta({
  layout: 'professional',
  middleware: ['auth', 'role'],
  roles: ['professional'],
})
</script>

<template>
  <v-card rounded="xl">
    <v-card-item>
      <v-card-title>Agenda profesional</v-card-title>
      <v-card-subtitle>
        Pendiente de conectar a endpoints de agenda profesional.
      </v-card-subtitle>
    </v-card-item>

    <v-card-text>
      Esta pantalla debe evolucionar a listado de citas, filtros por estado, inicio de teleconsulta y acceso a nota clínica.
    </v-card-text>
  </v-card>
</template>
```

---

### Archivo 2: `web_frontend/pages/admin/moderation/cases.vue`

```vue
<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_validation', 'admin_support', 'admin_moderation', 'admin_privacy'],
})
</script>

<template>
  <v-card rounded="xl">
    <v-card-item>
      <v-card-title>Casos de moderación</v-card-title>
      <v-card-subtitle>
        Pantalla base para futura conexión de cola de denuncias y revisión.
      </v-card-subtitle>
    </v-card-item>

    <v-card-text>
      Se debe conectar a endpoints reales de denuncias, revisión, decisión y bitácora cuando esa fase sea implementada.
    </v-card-text>
  </v-card>
</template>
```

---

### Archivo 3: `web_frontend/pages/admin/moderation/sanctions.vue`

```vue
<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_validation', 'admin_support', 'admin_moderation', 'admin_privacy'],
})
</script>

<template>
  <v-card rounded="xl">
    <v-card-item>
      <v-card-title>Sanciones</v-card-title>
      <v-card-subtitle>
        Pantalla base para gestión de sanciones futuras.
      </v-card-subtitle>
    </v-card-item>

    <v-card-text>
      Se debe conectar a endpoints de suspensión, restricción, levantamiento y auditoría cuando exista la fase de moderación.
    </v-card-text>
  </v-card>
</template>
```

---

### Archivo 4: `web_frontend/pages/admin/payments/settlements.vue`

```vue
<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_validation', 'admin_support', 'admin_moderation', 'admin_privacy'],
})
</script>

<template>
  <v-card rounded="xl">
    <v-card-item>
      <v-card-title>Settlements</v-card-title>
      <v-card-subtitle>
        Pantalla base para fase financiera administrativa.
      </v-card-subtitle>
    </v-card-item>

    <v-card-text>
      Se debe conectar a endpoints reales de liquidaciones, conciliación, estado y exportación cuando la fase financiera quede cerrada.
    </v-card-text>
  </v-card>
</template>
```

---

## 4) Instrucción cerrada para pasar al programador

```text
IMPLEMENTAR ÚNICAMENTE EL SIGUIENTE BLOQUE Y NADA MÁS.

RESTRICCIÓN ABSOLUTA DE ALCANCE

- NO tocar backend.
- NO tocar migraciones.
- NO tocar web_frontend/composables/useApi.ts.
- NO tocar stores, middleware, layouts, auth, login, register, privacidad, búsqueda, citas del paciente, checkout, pagos del paciente, precios del profesional, earnings del profesional, teleconsulta ni ninguna otra pantalla.
- NO crear endpoints.
- NO refactorizar archivos fuera de los 4 indicados.
- NO aprovechar para arreglar otras cosas.
- SOLO reemplazar exactamente estos 4 archivos:

1. web_frontend/pages/professional/appointments.vue
2. web_frontend/pages/admin/moderation/cases.vue
3. web_frontend/pages/admin/moderation/sanctions.vue
4. web_frontend/pages/admin/payments/settlements.vue

OBJETIVO

- Dejar estas 4 pantallas en estado base mínimo funcional.
- Mantener definePageMeta, layout, middleware y roles correctos.
- Dejar texto explícito de que la conexión real a endpoints se hará después.
- NO implementar lógica de negocio.
- NO simular datos.
- NO crear componentes extra.
- NO crear composables extra.
```

Eso coincide con lo que el propio repo define para este tramo. 

---

## 5) Pruebas de verificación y regresión

### Levantar frontend

```bash
cd web_frontend
npm install
NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1 npm run dev
```

Ese comando también está alineado con el repo para este bloque. 

### Checklist de no-rotura

1. El login debe seguir funcionando igual.
2. La redirección por rol debe seguir enviando:

   * admin → `/admin/dashboard`
   * professional → `/professional/dashboard`
3. La búsqueda de profesionales del paciente debe seguir funcionando.
4. El detalle del profesional debe seguir funcionando.
5. La reserva de citas del paciente no debe romperse.
6. Las pantallas de privacidad ya cerradas no deben cambiar comportamiento.
7. Las 4 pantallas nuevas deben abrir sin error de compilación.
8. No deben aparecer imports nuevos ni dependencias nuevas.

### Verificación manual de rutas

* `/professional/appointments`
* `/admin/moderation/cases`
* `/admin/moderation/sanctions`
* `/admin/payments/settlements`

Resultado esperado:

* Carga correcta del layout.
* Middleware funcionando.
* Sin errores 500 del frontend.
* Sin llamadas API nuevas.

---

## 6) Plan de reversión

### Reversión rápida con Git

```bash
git restore web_frontend/pages/professional/appointments.vue
git restore web_frontend/pages/admin/moderation/cases.vue
git restore web_frontend/pages/admin/moderation/sanctions.vue
git restore web_frontend/pages/admin/payments/settlements.vue
```

### Reversión con backups directos

```bash
cp /tmp/appointments.vue.bak web_frontend/pages/professional/appointments.vue
cp /tmp/cases.vue.bak web_frontend/pages/admin/moderation/cases.vue
cp /tmp/sanctions.vue.bak web_frontend/pages/admin/moderation/sanctions.vue
cp /tmp/settlements.vue.bak web_frontend/pages/admin/payments/settlements.vue
```

### Emergencia total

```bash
git reset --hard HEAD~1
```

---

Después de este bloque, si ya queda aplicado, el siguiente frente serio para hoy o mañana sería preparar el **paso 9 de IA segura y útil**, porque el repo lo deja como la siguiente fase real, no clínica y auditada. 

Archivo revisado: [repomix_buscamedicos_full_ai.xml](sandbox:/mnt/data/repomix_buscamedicos_full_ai.xml) 
