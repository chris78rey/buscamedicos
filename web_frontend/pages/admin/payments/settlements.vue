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
