import type { RoleCode } from '~/types/auth'

export default defineNuxtRouteMiddleware(async (to) => {
  const expectedRoles = (to.meta.roles ?? []) as RoleCode[]
  if (!expectedRoles.length) {
    return
  }

  const { bootstrapAuth, resolveRoleHome } = useAuth()
  const authStore = await bootstrapAuth()

  if (!authStore.isAuthenticated || !authStore.user) {
    return navigateTo(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }

  if (expectedRoles.some(role => authStore.roleCodes.includes(role))) {
    return
  }

  return navigateTo(resolveRoleHome(authStore.roleCodes))
})
