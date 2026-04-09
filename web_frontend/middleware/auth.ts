export default defineNuxtRouteMiddleware(async (to) => {
  const { bootstrapAuth } = useAuth()
  const authStore = await bootstrapAuth()

  if (!authStore.isAuthenticated || !authStore.user) {
    const redirect = encodeURIComponent(to.fullPath)
    return navigateTo(`/login?redirect=${redirect}`)
  }
})
