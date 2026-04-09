export default defineNuxtRouteMiddleware(async () => {
  const { bootstrapAuth, resolveRoleHome } = useAuth()
  const authStore = await bootstrapAuth()

  if (authStore.isAuthenticated && authStore.user) {
    return navigateTo(resolveRoleHome(authStore.roleCodes))
  }
})
