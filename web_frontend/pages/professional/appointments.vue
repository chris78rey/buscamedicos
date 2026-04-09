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
