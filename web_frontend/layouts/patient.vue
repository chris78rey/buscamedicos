<script setup lang="ts">
const authStore = useAuthStore()

const links = [
  { title: 'Dashboard', to: '/patient/dashboard', icon: 'mdi-view-dashboard' },
  { title: 'Profesionales', to: '/patient/professionals', icon: 'mdi-stethoscope' },
  { title: 'Citas', to: '/patient/appointments', icon: 'mdi-calendar-check' },
  { title: 'Pagos', to: '/patient/payments', icon: 'mdi-credit-card-outline' },
  { title: 'Privacidad', to: '/patient/privacy/consents', icon: 'mdi-shield-account' },
]

async function handleLogout() {
  authStore.logout()
  await navigateTo('/login')
}
</script>

<template>
  <v-app>
    <v-navigation-drawer permanent>
      <v-list density="comfortable" nav>
        <v-list-item title="Panel paciente" subtitle="BuscaMedicos" />
        <v-divider class="my-2" />
        <v-list-item
          v-for="link in links"
          :key="link.to"
          :prepend-icon="link.icon"
          :title="link.title"
          :to="link.to"
          rounded="lg"
        />
      </v-list>
    </v-navigation-drawer>

    <v-main class="bg-grey-lighten-4">
      <v-container class="py-8">
        <div class="d-flex justify-space-between align-center mb-6">
          <div>
            <h1 class="text-h5 font-weight-bold">Paciente</h1>
            <p class="text-body-2 text-medium-emphasis mb-0">
              {{ authStore.user?.email ?? 'Sesion activa' }}
            </p>
          </div>
          <v-btn color="primary" variant="outlined" @click="handleLogout">
            Cerrar sesion
          </v-btn>
        </div>
        <slot />
      </v-container>
    </v-main>
  </v-app>
</template>
