<script setup lang="ts">
definePageMeta({
  layout: 'professional',
  middleware: ['auth', 'role'],
  roles: ['professional'],
})

const cards = [
  {
    title: 'Perfil y agenda',
    text: 'Configura nombre público, perfil visible, horarios semanales y bloqueos puntuales para habilitar reservas reales.',
    to: '/professional/agenda',
    icon: 'mdi-calendar-clock-outline',
  },
  {
    title: 'Citas',
    text: 'Revisa agenda, estados y seguimiento clínico inicial.',
    to: '/professional/appointments',
    icon: 'mdi-calendar-account',
  },
  {
    title: 'Precios',
    text: 'Administra valores operativos por modalidad para el flujo económico.',
    to: '/professional/prices',
    icon: 'mdi-cash-multiple',
  },
  {
    title: 'Teleconsulta',
    text: 'Prepara el acceso a sesiones virtuales y herramientas clínicas.',
    to: '/professional/teleconsultation/demo-appointment',
    icon: 'mdi-video-outline',
  },
  {
    title: 'Privacidad',
    text: 'Consulta accesos y solicita acceso excepcional cuando aplique.',
    to: '/professional/privacy/access-logs',
    icon: 'mdi-file-lock-outline',
  },
]
</script>

<template>
  <v-row>
    <v-col v-for="card in cards" :key="card.to" cols="12" md="6" lg="4">
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
