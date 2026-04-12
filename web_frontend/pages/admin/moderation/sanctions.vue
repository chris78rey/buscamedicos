<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_moderation'],
})

const rows = [
  {
    module: 'Sanciones activas',
    detail: 'Advertencias, suspensiones temporales y restricciones de visibilidad.',
    state: 'Pendiente',
  },
  {
    module: 'Historial',
    detail: 'Consulta cronológica de sanciones aplicadas, levantadas o expiradas.',
    state: 'Pendiente',
  },
  {
    module: 'Levantamiento',
    detail: 'Acción administrativa para levantar sanciones y registrar motivo.',
    state: 'Pendiente',
  },
]
</script>

<template>
  <v-container>
    <div class="d-flex align-center justify-space-between flex-wrap ga-4 mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold mb-2">Sanciones</h1>
        <p class="text-subtitle-1 text-medium-emphasis">
          Estructura mínima para administración de sanciones mientras se conecta el flujo definitivo.
        </p>
      </div>

      <v-chip color="warning" variant="flat">
        Placeholder funcional
      </v-chip>
    </div>

    <v-card rounded="xl" elevation="2">
      <v-table>
        <thead>
          <tr>
            <th>Módulo</th>
            <th>Detalle</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.module">
            <td class="font-weight-medium">{{ row.module }}</td>
            <td>{{ row.detail }}</td>
            <td>
              <v-chip size="small" color="grey-darken-1" variant="tonal">
                {{ row.state }}
              </v-chip>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    <v-alert
      class="mt-6"
      type="info"
      variant="tonal"
      border="start"
      title="Siguiente conexión"
      text="Esta pantalla debe conectarse después con listar sanciones, crear sanción y levantar sanción."
    />
  </v-container>
</template>
