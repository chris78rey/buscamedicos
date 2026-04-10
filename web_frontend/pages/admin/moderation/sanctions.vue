<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_moderation'],
})
</script>

<template>
  <v-container>
    <h1 class="text-h4 font-weight-bold mb-2">Historial de Sanciones</h1>
    <p class="text-subtitle-1 text-medium-emphasis mb-6">Registro de amonestaciones, suspensiones y expulsiones del sistema.</p>

    <v-card rounded="xl" elevation="2">
      <v-table>
        <thead>
          <tr>
            <th>Usuario</th>
            <th>Tipo</th>
            <th>Motivo</th>
            <th>Fecha</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td colspan="5" class="text-center py-8 text-medium-emphasis italic">
              No se han emitido sanciones en los últimos 30 días.
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>
  </v-container>
</template>
