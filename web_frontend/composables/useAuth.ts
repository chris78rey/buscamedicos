import type { CurrentUser, RoleCode } from '~/types/auth'

const adminRoleCodes: RoleCode[] = [
  'super_admin',
  'admin_validation',
  'admin_support',
  'admin_moderation',
  'admin_privacy',
]

export function useAuth() {
  function getRoleCodes(user: CurrentUser | null | undefined): RoleCode[] {
    if (!user) {
      return []
    }

    if (user.role_codes?.length) {
      return user.role_codes
    }

    return user.roles?.map(role => role.code) ?? []
  }

  function isAdminRole(role: RoleCode): boolean {
    return adminRoleCodes.includes(role)
  }

  function resolveRoleHome(roles: RoleCode[]): string {
    if (roles.includes('privacy_auditor')) {
      return '/privacy-auditor/access-logs'
    }

    if (roles.some(isAdminRole)) {
      return '/admin/dashboard'
    }

    if (roles.includes('professional')) {
      return '/professional/dashboard'
    }

    return '/patient/dashboard'
  }

  async function bootstrapAuth() {
    const authStore = useAuthStore()
    if (!authStore.loaded) {
      await authStore.bootstrap()
    }
    return authStore
  }

  return {
    adminRoleCodes,
    bootstrapAuth,
    getRoleCodes,
    isAdminRole,
    resolveRoleHome,
  }
}
