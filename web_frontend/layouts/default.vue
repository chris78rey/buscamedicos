<script setup lang="ts">
const authStore = useAuthStore()
const { bootstrapAuth, resolveRoleHome } = useAuth()

await bootstrapAuth()

const primaryLink = computed(() => {
  if (!authStore.user) {
    return { label: 'Login', to: '/login' }
  }

  return {
    label: 'Dashboard',
    to: resolveRoleHome(authStore.roleCodes),
  }
})

async function handleLogout() {
  authStore.logout()
  await navigateTo('/login')
}
</script>

<template>
  <v-app>
    <v-app-bar color="primary" density="comfortable">
      <v-app-bar-title>BuscaMedicos Web</v-app-bar-title>

      <v-btn to="/" variant="text">
        Inicio
      </v-btn>
      <v-btn :to="primaryLink.to" variant="text">
        {{ primaryLink.label }}
      </v-btn>
      <v-btn v-if="!authStore.user" to="/register" variant="text">
        Registro
      </v-btn>
      <v-spacer />
      <v-btn v-if="authStore.user" variant="text" @click="handleLogout">
        Cerrar sesion
      </v-btn>
    </v-app-bar>

    <v-main>
      <slot />
    </v-main>
  </v-app>
</template>
