<script setup lang="ts">
const authStore = useAuthStore()

const links = [
  { title: 'Dashboard', to: '/admin/dashboard', icon: 'mdi-view-dashboard' },
  { title: 'Privacidad', to: '/admin/privacy/access-logs', icon: 'mdi-shield-search' },
  { title: 'Moderacion', to: '/admin/moderation/cases', icon: 'mdi-gavel' },
  { title: 'Pagos', to: '/admin/payments/settlements', icon: 'mdi-cash-multiple' },
]

async function handleLogout() {
  authStore.logout()
  await navigateTo('/login')
}
</script>

<template>
  <v-app>
    <v-navigation-drawer permanent color="teal-darken-4">
      <v-list bg-color="teal-darken-4" density="comfortable" nav>
        <v-list-item title="Panel admin" subtitle="BuscaMedicos" />
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

    <v-main class="bg-teal-lighten-5">
      <v-container class="py-8">
        <div class="d-flex justify-space-between align-center mb-6">
          <div>
            <h1 class="text-h5 font-weight-bold">Administracion</h1>
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
