<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_moderation'],
})
</script>

<template>
  <v-container>
    <h1 class="text-h4 font-weight-bold mb-2">Cola de Moderación</h1>
    <p class="text-subtitle-1 text-medium-emphasis mb-6">Gestiona denuncias y reportes de comportamiento en la plataforma.</p>

    <v-card rounded="xl" class="pa-10 text-center border-dashed" variant="outlined">
      <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-shield-alert-outline</v-icon>
      <h3 class="text-h6 font-weight-bold">Sin reportes pendientes</h3>
      <p class="text-body-2 text-medium-emphasis mx-auto" style="max-width: 400px;">
        Actualmente no existen denuncias de pacientes ni profesionales que requieran intervención inmediata.
      </p>
    </v-card>
  </v-container>
</template>

<style scoped>
.border-dashed {
  border: 2px dashed #e0e0e0 !important;
}
</style>
