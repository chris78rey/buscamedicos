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
