#### Impacto y riesgos

El CRUD de agenda **sí existe** en backend y frontend. El problema no parece ser “faltan endpoints”, sino una desalineación de datos o validación en ejecución. El frontend de `professional/agenda.vue` sí llama a `createAvailability()` contra `/professionals/me/availabilities`, y el backend sí expone `POST /me/availabilities`.  

El riesgo real aquí es tocar demasiado. Lo más conservador es corregir primero el flujo mínimo que puede estar fallando por:

* modalidad enviada desde frontend que no existe para ese profesional;
* `weekday` fuera del rango esperado por backend;
* horarios duplicados o traslapados;
* profesional autenticado sin registro real asociado;
* error de validación silencioso porque el frontend solo muestra “No se pudo guardar la disponibilidad”. 

También hay una pista fuerte: el frontend usa por defecto `modality_code: 'in_person_consultorio'`, y si las modalidades reales del profesional no incluyen ese código, el backend puede rechazar la creación. El propio frontend ya carga modalidades desde `getMyModalities()`, así que conviene validar contra ese catálogo antes de guardar. 

---

#### Preparación

Antes de cambiar nada:

```bash
cp web_frontend/pages/professional/agenda.vue web_frontend/pages/professional/agenda.vue.bak
cp web_frontend/composables/useProfessionalAgenda.ts web_frontend/composables/useProfessionalAgenda.ts.bak
```

Diagnóstico previo recomendado en navegador:

1. abrir DevTools;
2. ir a Network;
3. presionar **Agregar disponibilidad**;
4. revisar el status del `POST /professionals/me/availabilities`.

Lectura rápida:

* `401/403`: problema de sesión o rol;
* `404`: el usuario tiene rol `professional`, pero no tiene fila real en `professionals`;
* `400/422`: problema de payload;
* `409`: traslape de disponibilidad.
  Eso ya estaba identificado como el diagnóstico correcto para esta agenda. 

---

#### Fase 1

**Objetivo**
Dejar visible el error real del backend y evitar envío de modalidad inválida.

**Riesgo controlado**
Solo se toca frontend.

**Archivo a tocar**
`web_frontend/pages/professional/agenda.vue`

**Problema puntual**
El mensaje actual es demasiado genérico: “No se pudo guardar la disponibilidad”. Así no se sabe si el backend respondió `404`, `409` o `422`. Además, el formulario arranca con una modalidad fija que puede no existir para el profesional actual. 

**Cambio exacto 1: mejorar el mensaje de error**

Buscar la función `resolveError(error: unknown, fallback: string)` y reemplazarla por esta:

```ts
/* INICIO CAMBIO NUEVO */
function resolveError(error: unknown, fallback: string) {
  if (error instanceof FetchError) {
    const detail = error.data?.detail

    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }

    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item: any) => item?.msg || JSON.stringify(item))
        .join(' | ')
    }

    const status = error.response?.status
    if (status === 404) {
      return 'No existe perfil profesional asociado a este usuario.'
    }
    if (status === 409) {
      return 'La disponibilidad se traslapa con otra ya registrada.'
    }
    if (status === 422) {
      return 'Los datos enviados no cumplen el formato esperado por el backend.'
    }

    return fallback
  }

  return fallback
}
/* FIN CAMBIO NUEVO */
```

**Cambio exacto 2: asegurar modalidad válida cargada desde backend**

Dentro de la carga inicial de modalidades, cuando se cargue `getMyModalities()`, agregar esta validación:

```ts
/* INICIO CAMBIO NUEVO */
async function loadModalities() {
  try {
    const items = await getMyModalities()
    if (Array.isArray(items) && items.length > 0) {
      modalityOptions.value = items

      const exists = items.some(item => item.code === availabilityForm.modality_code)
      if (!exists) {
        availabilityForm.modality_code = items[0]?.code || 'teleconsulta'
      }
    }
  }
  catch {
    modalityOptions.value = [
      { id: 'fallback-in-person', code: 'in_person_consultorio', name: 'Consulta presencial' },
      { id: 'fallback-tele', code: 'teleconsulta', name: 'Teleconsulta' },
    ]
  }
}
/* FIN CAMBIO NUEVO */
```

Y en la carga general, asegurarse de llamar `await loadModalities()` antes de usar el formulario.

---

#### Prueba de Fase 1

**Cómo probar**

1. entrar como `prof_val@demo.com`;
2. abrir Agenda;
3. intentar guardar;
4. verificar que el mensaje ahora diga la causa real;
5. confirmar que el combo de modalidad use una modalidad real cargada del backend.

**Qué debe seguir funcionando**

* listado de disponibilidades;
* bloqueos puntuales;
* botón de recargar.

**Cómo revertir esa fase**

```bash
cp web_frontend/pages/professional/agenda.vue.bak web_frontend/pages/professional/agenda.vue
```

---

#### Fase 2

**Objetivo**
Validar antes de enviar y no disparar requests que el backend necesariamente rechazará.

**Riesgo controlado**
Solo validación local.

**Archivo a tocar**
`web_frontend/pages/professional/agenda.vue`

**Agregar estas funciones:**

```ts
/* INICIO CAMBIO NUEVO */
function isValidTimeRange(startTime: string, endTime: string) {
  return startTime < endTime
}

function hasValidSlotMinutes(value: number) {
  return [15, 20, 30, 45, 60].includes(value)
}

function hasValidWeekday(value: number) {
  return Number.isInteger(value) && value >= 0 && value <= 6
}
/* FIN CAMBIO NUEVO */
```

**Y dentro de la función que guarda disponibilidad, antes del `createAvailability` o `updateAvailability`, agregar:**

```ts
/* INICIO CAMBIO NUEVO */
clearMessages()

if (!hasValidWeekday(availabilityForm.weekday)) {
  errorMessage.value = 'El día seleccionado no es válido.'
  return
}

if (!hasValidSlotMinutes(availabilityForm.slot_minutes)) {
  errorMessage.value = 'La duración del slot debe ser 15, 20, 30, 45 o 60 minutos.'
  return
}

if (!isValidTimeRange(availabilityForm.start_time, availabilityForm.end_time)) {
  errorMessage.value = 'La hora de inicio debe ser menor que la hora de fin.'
  return
}

const modalityExists = modalityOptions.value.some(
  item => item.code === availabilityForm.modality_code,
)

if (!modalityExists) {
  errorMessage.value = 'La modalidad seleccionada no existe para este profesional.'
  return
}
/* FIN CAMBIO NUEVO */
```

Esto baja bastante los rechazos obvios.

---

#### Prueba de Fase 2

**Cómo probar**

1. poner hora inicio 12:00 y fin 08:00;
2. intentar guardar;
3. verificar mensaje local;
4. poner modalidad válida;
5. volver a guardar;
6. revisar si ya avanza al backend.

**Qué debe seguir funcionando**

* edición;
* recarga;
* alta de bloqueos.

**Cómo revertir esa fase**
Restaurar backup.

---

#### Fase 3

**Objetivo**
Confirmar el caso 404 más probable: usuario con rol profesional pero sin perfil profesional asociado.

**Riesgo controlado**
Sin cambios de base de datos todavía; solo diagnóstico y, si aplica, seed o reparación puntual.

**Archivo / módulo relacionado**
`backend_api/app/routers/professional_self.py`

**Hallazgo**
Toda la agenda depende de obtener primero el profesional autenticado. Si no existe fila en `professionals`, el backend responde con 404 y ninguna operación de agenda puede guardar. Eso ya estaba identificado como causa probable del fallo de CRUD. 

**Cómo probar**
Con el token del profesional activo, llamar al endpoint de perfil:

```bash
GET /api/v1/professionals/me
```

Si eso devuelve 404, el problema no está en la agenda sino en la relación usuario-profesional.

**Acción conservadora**
No tocar agenda todavía; primero corregir datos del usuario demo para que sí tenga registro en `professionals`.

El seed del proyecto sí crea profesionales demo con disponibilidades para ambas modalidades, incluido `in_person_consultorio` y `teleconsulta`. Eso indica que, si el usuario demo fue creado por seed completo, debería funcionar. Si no funciona, puede que ese usuario no corresponda a un profesional realmente sembrado o que la BD esté en estado parcial. 

---

#### Prueba de Fase 3

**Cómo probar**

1. ejecutar `GET /api/v1/professionals/me`;
2. si responde 200, seguir con agenda;
3. si responde 404, corregir el usuario demo o volver a sembrar datos.

Comandos útiles:

```bash
docker logs buscamedicos_backend --tail 200
docker exec buscamedicos_backend sh -c "cd /app && PYTHONPATH=/app python scripts/seed.py"
```

---

#### Pruebas de regresión

Después de estas fases:

1. crear disponibilidad;
2. editar disponibilidad;
3. eliminar disponibilidad;
4. crear bloqueo puntual;
5. eliminar bloqueo;
6. recargar pantalla;
7. verificar que la lista se refresque.

Además revisar si el backend devuelve `409` cuando se intenta crear un horario superpuesto, porque ese sería comportamiento correcto, no bug. 

---

#### Plan de reversión total

```bash
cp web_frontend/pages/professional/agenda.vue.bak web_frontend/pages/professional/agenda.vue
cp web_frontend/composables/useProfessionalAgenda.ts.bak web_frontend/composables/useProfessionalAgenda.ts
```

Si también se resembró base de datos y se quiere volver atrás, ahí ya tocaría restaurar la BD o recrear el entorno.

---

### Diagnóstico más probable

Por lo que se ve, hay tres causas candidatas y el orden más probable es este:

1. **modalidad inválida o no disponible para el profesional actual**;
2. **respuesta 404 porque el usuario autenticado no tiene fila real en `professionals`**;
3. **traslape o validación del backend (`409` o `422`) que el frontend está ocultando detrás del mensaje genérico**.   

Si se quiere, en el siguiente mensaje se puede dejar el bloque completo de `web_frontend/pages/professional/agenda.vue` ya corregido para pegar directamente.




---
---


#### Impacto y riesgos

La pantalla de agenda del profesional sí tiene CRUD implementado, pero hoy está fallando por dos cosas muy concretas:

* el frontend muestra un error genérico y oculta la causa real del backend; 
* el backend sí valida disponibilidad, traslapes y existencia del profesional, por lo que puede devolver `404`, `409` o `422` legítimamente.

Además, el seed del proyecto sí crea disponibilidades demo para `in_person_consultorio` y `teleconsulta`, así que si el usuario demo está bien sembrado, esas modalidades deberían funcionar. 

El cambio mínimo y seguro consiste en:

* mejorar el manejo de errores en `agenda.vue`;
* validar localmente antes de enviar;
* asegurar que la modalidad usada exista en las modalidades cargadas.

No se toca base de datos ni backend.

---

#### Preparación

Hacer respaldo del archivo:

```bash
cp web_frontend/pages/professional/agenda.vue web_frontend/pages/professional/agenda.vue.bak
```

Validación previa útil:

```bash
docker logs buscamedicos_backend --tail 200
```

Y en navegador:

* abrir DevTools;
* pestaña Network;
* intentar guardar disponibilidad;
* revisar el `POST /api/v1/professionals/me/availabilities`.

---

#### Fase 1

**Objetivo**
Mostrar el error real del backend y evitar que la pantalla se quede con un mensaje ambiguo.

**Riesgo controlado**
Solo se toca frontend.

**Archivo a tocar**
`web_frontend/pages/professional/agenda.vue`

**Código exacto**

Buscar la función actual `resolveError` y reemplazarla completa por esto:

```ts
/* INICIO CAMBIO NUEVO */
function resolveError(error: unknown, fallback: string) {
  if (error instanceof FetchError) {
    const detail = error.data?.detail

    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }

    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item: any) => item?.msg || JSON.stringify(item))
        .join(' | ')
    }

    const status = error.response?.status
    if (status === 404) {
      return 'No existe perfil profesional asociado a este usuario.'
    }
    if (status === 409) {
      return 'La disponibilidad se traslapa con otra ya registrada.'
    }
    if (status === 422) {
      return 'Los datos enviados no cumplen el formato esperado por el backend.'
    }

    return fallback
  }

  return fallback
}
/* FIN CAMBIO NUEVO */
```

**Cómo probar**

Intentar guardar otra vez una disponibilidad.

**Resultado esperado**
La franja roja ya no dirá solo “No se pudo guardar la disponibilidad”, sino la causa real.

**Qué debe seguir funcionando**

* recargar agenda;
* listar disponibilidades;
* crear bloqueos puntuales.

**Cómo revertir esa fase**

```bash
cp web_frontend/pages/professional/agenda.vue.bak web_frontend/pages/professional/agenda.vue
```

---

#### Prueba de Fase 1

Si aparece alguno de estos mensajes, ya habrá diagnóstico real:

* `No existe perfil profesional asociado a este usuario`
* `La disponibilidad se traslapa con otra ya registrada`
* `Los datos enviados no cumplen el formato esperado por el backend`

Eso confirmará que el CRUD sí está llegando al backend.

---

#### Fase 2

**Objetivo**
Evitar enviar formularios inválidos que el backend rechazará de todas formas.

**Riesgo controlado**
Solo validación local.

**Archivo a tocar**
`web_frontend/pages/professional/agenda.vue`

**Código exacto**

Agregar estas funciones debajo de la sección de utilidades del script:

```ts
/* INICIO CAMBIO NUEVO */
function isValidTimeRange(startTime: string, endTime: string) {
  return Boolean(startTime) && Boolean(endTime) && startTime < endTime
}

function hasValidSlotMinutes(value: number) {
  return [15, 20, 30, 45, 60].includes(Number(value))
}

function hasValidWeekday(value: number) {
  return Number.isInteger(Number(value)) && Number(value) >= 0 && Number(value) <= 6
}
/* FIN CAMBIO NUEVO */
```

Ahora buscar la función que guarda la disponibilidad, normalmente `submitAvailability` o equivalente, y **antes** del `await createAvailability(...)` o `await updateAvailability(...)` agregar esto:

```ts
/* INICIO CAMBIO NUEVO */
availabilityError.value = null
availabilitySuccess.value = null

if (!hasValidWeekday(Number(availabilityForm.weekday))) {
  availabilityError.value = 'El día seleccionado no es válido.'
  return
}

if (!hasValidSlotMinutes(Number(availabilityForm.slot_minutes))) {
  availabilityError.value = 'La duración del slot debe ser 15, 20, 30, 45 o 60 minutos.'
  return
}

if (!isValidTimeRange(availabilityForm.start_time, availabilityForm.end_time)) {
  availabilityError.value = 'La hora de inicio debe ser menor que la hora de fin.'
  return
}

const modalityExists = modalityOptions.value.some(
  item => item.code === availabilityForm.modality_code,
)

if (!modalityExists) {
  availabilityError.value = 'La modalidad seleccionada no existe para este profesional.'
  return
}
/* FIN CAMBIO NUEVO */
```

> Si el archivo usa otros nombres como `formError`, `errorMessage`, `successMessage` o `availabilityState.error`, se debe adaptar solo el nombre de esas dos variables, sin cambiar la lógica.

**Cómo probar**

* poner hora fin menor que hora inicio;
* poner un slot inválido;
* intentar guardar.

**Resultado esperado**
El frontend debe frenar el envío antes del request.

**Qué debe seguir funcionando**

* edición visual del formulario;
* carga de modalidades;
* recarga de datos.

**Cómo revertir esa fase**
Restaurar backup.

---

#### Prueba de Fase 2

La pantalla debe impedir:

* `12:00` a `08:00`;
* slot de `10` minutos;
* día fuera de rango;
* modalidad inexistente.

Esto además queda alineado con las reglas del proyecto: `start_time < end_time` y `slot_minutes` permitido solo en `15, 20, 30, 45, 60`. 

---

#### Fase 3

**Objetivo**
Asegurar que la modalidad inicial del formulario siempre exista en el catálogo cargado.

**Riesgo controlado**
Solo inicialización del formulario.

**Archivo a tocar**
`web_frontend/pages/professional/agenda.vue`

**Código exacto**

Buscar la parte donde se cargan modalidades desde `getMyModalities()` y reemplazar esa carga por esta versión conservadora:

```ts
/* INICIO CAMBIO NUEVO */
async function loadModalities() {
  try {
    const items = await getMyModalities()

    if (Array.isArray(items) && items.length > 0) {
      modalityOptions.value = items

      const exists = items.some(item => item.code === availabilityForm.modality_code)
      if (!exists) {
        availabilityForm.modality_code = items[0]?.code || 'teleconsulta'
      }

      return
    }

    modalityOptions.value = [
      { id: 'fallback-1', code: 'in_person_consultorio', name: 'Consulta en consultorio' },
      { id: 'fallback-2', code: 'teleconsulta', name: 'Teleconsulta' },
    ]

    if (!availabilityForm.modality_code) {
      availabilityForm.modality_code = modalityOptions.value[0].code
    }
  }
  catch {
    modalityOptions.value = [
      { id: 'fallback-1', code: 'in_person_consultorio', name: 'Consulta en consultorio' },
      { id: 'fallback-2', code: 'teleconsulta', name: 'Teleconsulta' },
    ]

    if (!availabilityForm.modality_code) {
      availabilityForm.modality_code = modalityOptions.value[0].code
    }
  }
}
/* FIN CAMBIO NUEVO */
```

Y en la carga inicial de la página, asegurarse de que se ejecute `await loadModalities()` antes de usar el formulario.

**Cómo probar**

* abrir agenda;
* confirmar que el select de modalidad tenga una opción válida;
* guardar disponibilidad con esa modalidad.

**Qué debe seguir funcionando**

* lista de modalidades;
* creación de disponibilidad;
* recarga de la vista.

**Cómo revertir esa fase**
Restaurar backup.

---

#### Prueba de Fase 3

Si el seed está bien aplicado, las modalidades válidas esperadas son `in_person_consultorio` y `teleconsulta`. El proyecto ya las siembra para profesionales demo. 

---

#### Pruebas de regresión

Después de las tres fases:

1. crear disponibilidad;
2. recargar;
3. volver a crear una igual y confirmar que el sistema muestre traslape si aplica;
4. eliminar disponibilidad;
5. crear bloqueo puntual;
6. recargar otra vez.

Validación adicional:

```bash
docker logs buscamedicos_backend --tail 200
```

Si sigue fallando, el status HTTP real ya permitirá saber si el problema es:

* `404` profesional inexistente;
* `409` traslape;
* `422` payload inválido.

---

#### Plan de reversión total

```bash
cp web_frontend/pages/professional/agenda.vue.bak web_frontend/pages/professional/agenda.vue
```

Luego reiniciar frontend:

```bash
cd web_frontend
npm run dev
```

---

### Bloque listo para copiar

A continuación se deja el bloque operativo que se puede pasar al programador para pegar en `web_frontend/pages/professional/agenda.vue`.

```ts
/* INICIO CAMBIO NUEVO */
function resolveError(error: unknown, fallback: string) {
  if (error instanceof FetchError) {
    const detail = error.data?.detail

    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }

    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item: any) => item?.msg || JSON.stringify(item))
        .join(' | ')
    }

    const status = error.response?.status
    if (status === 404) {
      return 'No existe perfil profesional asociado a este usuario.'
    }
    if (status === 409) {
      return 'La disponibilidad se traslapa con otra ya registrada.'
    }
    if (status === 422) {
      return 'Los datos enviados no cumplen el formato esperado por el backend.'
    }

    return fallback
  }

  return fallback
}

function isValidTimeRange(startTime: string, endTime: string) {
  return Boolean(startTime) && Boolean(endTime) && startTime < endTime
}

function hasValidSlotMinutes(value: number) {
  return [15, 20, 30, 45, 60].includes(Number(value))
}

function hasValidWeekday(value: number) {
  return Number.isInteger(Number(value)) && Number(value) >= 0 && Number(value) <= 6
}

async function loadModalities() {
  try {
    const items = await getMyModalities()

    if (Array.isArray(items) && items.length > 0) {
      modalityOptions.value = items

      const exists = items.some(item => item.code === availabilityForm.modality_code)
      if (!exists) {
        availabilityForm.modality_code = items[0]?.code || 'teleconsulta'
      }

      return
    }

    modalityOptions.value = [
      { id: 'fallback-1', code: 'in_person_consultorio', name: 'Consulta en consultorio' },
      { id: 'fallback-2', code: 'teleconsulta', name: 'Teleconsulta' },
    ]

    if (!availabilityForm.modality_code) {
      availabilityForm.modality_code = modalityOptions.value[0].code
    }
  }
  catch {
    modalityOptions.value = [
      { id: 'fallback-1', code: 'in_person_consultorio', name: 'Consulta en consultorio' },
      { id: 'fallback-2', code: 'teleconsulta', name: 'Teleconsulta' },
    ]

    if (!availabilityForm.modality_code) {
      availabilityForm.modality_code = modalityOptions.value[0].code
    }
  }
}
/* FIN CAMBIO NUEVO */
```

Y dentro de la función que guarda disponibilidad, justo antes de llamar al API:

```ts
/* INICIO CAMBIO NUEVO */
availabilityError.value = null
availabilitySuccess.value = null

if (!hasValidWeekday(Number(availabilityForm.weekday))) {
  availabilityError.value = 'El día seleccionado no es válido.'
  return
}

if (!hasValidSlotMinutes(Number(availabilityForm.slot_minutes))) {
  availabilityError.value = 'La duración del slot debe ser 15, 20, 30, 45 o 60 minutos.'
  return
}

if (!isValidTimeRange(availabilityForm.start_time, availabilityForm.end_time)) {
  availabilityError.value = 'La hora de inicio debe ser menor que la hora de fin.'
  return
}

const modalityExists = modalityOptions.value.some(
  item => item.code === availabilityForm.modality_code,
)

if (!modalityExists) {
  availabilityError.value = 'La modalidad seleccionada no existe para este profesional.'
  return
}
/* FIN CAMBIO NUEVO */
```

Base técnica revisada: la agenda usa el composable de profesional y el backend sí expone CRUD de disponibilidades; además el proyecto define reglas explícitas para disponibilidad y el seed ya crea modalidades y disponibilidades demo.

Archivo de contexto revisado:
