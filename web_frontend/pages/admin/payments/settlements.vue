<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_support'],
})
</script>

<template>
  <v-container>
    <h1 class="text-h4 font-weight-bold mb-2">Liquidaciones (Settlements)</h1>
    <p class="text-subtitle-1 text-medium-emphasis mb-6">Conciliación de pagos y transferencias a profesionales de la salud.</p>

    <v-row>
      <v-col cols="12" md="4" v-for="title in ['Total Pendiente', 'Enviado a banco', 'Comisiones BM']" :key="title">
        <v-card rounded="xl" elevation="2" class="pa-4">
          <div class="text-overline mb-1">{{ title }}</div>
          <div class="text-h4 font-weight-bold">$0.00</div>
          <div class="text-caption text-success">Corte actual</div>
        </v-card>
      </v-col>
    </v-row>

    <v-card rounded="xl" elevation="2" class="mt-6">
      <v-card-text class="text-center py-12">
        <v-icon size="48" color="primary" class="mb-2">mdi-cash-clock</v-icon>
        <div class="text-h6">Módulo Financiero en espera</div>
        <p class="text-body-2 text-medium-emphasis">Las liquidaciones automáticas se procesan los días lunes.</p>
      </v-card-text>
    </v-card>
  </v-container>
</template>
