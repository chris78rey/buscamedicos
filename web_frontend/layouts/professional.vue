<script setup lang="ts">
const authStore = useAuthStore()

const links = [
  { title: 'Dashboard', to: '/professional/dashboard', icon: 'mdi-view-dashboard' },
  { title: 'Citas', to: '/professional/appointments', icon: 'mdi-calendar-account' },
  { title: 'Precios', to: '/professional/prices', icon: 'mdi-cash-multiple' },
  { title: 'Ganancias', to: '/professional/earnings', icon: 'mdi-chart-line' },
  { title: 'Teleconsulta', to: '/professional/teleconsultation/demo-appointment', icon: 'mdi-video' },
  { title: 'Privacidad', to: '/professional/privacy/access-logs', icon: 'mdi-file-shield' },
]

async function handleLogout() {
  authStore.logout()
  await navigateTo('/login')
}
</script>

<template>
  <v-app>
    <v-navigation-drawer permanent color="blue-grey-darken-4">
      <v-list bg-color="blue-grey-darken-4" density="comfortable" nav>
        <v-list-item title="Panel profesional" subtitle="BuscaMedicos" />
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

    <v-main class="bg-blue-grey-lighten-5">
      <v-container class="py-8">
        <div class="d-flex justify-space-between align-center mb-6">
          <div>
            <h1 class="text-h5 font-weight-bold">Profesional</h1>
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
