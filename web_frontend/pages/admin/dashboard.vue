<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_validation', 'admin_support', 'admin_moderation', 'admin_privacy'],
})

const cards = [
  {
    title: 'Privacidad',
    text: 'Accede a logs, politicas e incidentes regulatorios.',
    to: '/admin/privacy/access-logs',
    icon: 'mdi-shield-search',
  },
  {
    title: 'Moderacion',
    text: 'Supervisa casos y sanciones en el ecosistema.',
    to: '/admin/moderation/cases',
    icon: 'mdi-gavel',
  },
  {
    title: 'Validación médica',
    text: 'Revisa y aprueba solicitudes de profesionales.',
    to: '/admin/validation/requests',
    icon: 'mdi-card-account-details-star',
  },
  {
    title: 'Pagos',
    text: 'Revisa settlements y operaciones del marketplace.',
    to: '/admin/payments/settlements',
    icon: 'mdi-cash-multiple',
  },
  {
    title: 'Staff y Usuarios',
    text: 'Administra cuentas de administradores y roles del sistema.',
    to: '/admin/users',
    icon: 'mdi-account-group-outline',
  },
]
const authStore = useAuthStore()

const visibleCards = computed(() => {
  return cards.filter(card => {
    if (card.to === '/admin/users') {
      return authStore.user?.role_codes?.includes('super_admin')
    }
    return true
  })
})
</script>

<template>
  <v-row>
    <v-col v-for="card in visibleCards" :key="card.to" cols="12" md="4">
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
