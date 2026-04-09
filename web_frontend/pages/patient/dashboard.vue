<script setup lang="ts">
definePageMeta({
  layout: 'patient',
  middleware: ['auth', 'role'],
  roles: ['patient'],
})

const cards = [
  {
    title: 'Buscar profesionales',
    text: 'Explora la oferta medica disponible y agenda atencion.',
    to: '/patient/professionals',
    icon: 'mdi-magnify',
  },
  {
    title: 'Mis citas',
    text: 'Consulta proximas atenciones y el historial del paciente.',
    to: '/patient/appointments',
    icon: 'mdi-calendar-check',
  },
  {
    title: 'Privacidad',
    text: 'Gestiona consentimientos y revisa accesos a tu informacion.',
    to: '/patient/privacy/consents',
    icon: 'mdi-shield-account',
  },
]
</script>

<template>
  <v-row>
    <v-col v-for="card in cards" :key="card.to" cols="12" md="4">
      <v-card class="h-100" rounded="xl">
        <v-card-item :prepend-icon="card.icon">
          <v-card-title>{{ card.title }}</v-card-title>
        </v-card-item>
        <v-card-text>{{ card.text }}</v-card-text>
        <v-card-actions>
          <v-btn :to="card.to" color="primary" variant="tonal">
            Abrir
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-col>
  </v-row>
</template>
