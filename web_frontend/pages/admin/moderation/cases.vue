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
