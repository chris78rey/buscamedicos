import { FetchError } from 'ofetch'
import { defineStore } from 'pinia'

import type { CurrentUser, RoleCode } from '~/types/auth'

type AuthState = {
  token: string | null
  user: CurrentUser | null
  loaded: boolean
}

function getRoleCodes(user: CurrentUser | null): RoleCode[] {
  if (!user) {
    return []
  }

  if (user.role_codes?.length) {
    return user.role_codes
  }

  return user.roles?.map(role => role.code) ?? []
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: null,
    user: null,
    loaded: false,
  }),

  getters: {
    roleCodes: (state): RoleCode[] => getRoleCodes(state.user),
    isAuthenticated: (state): boolean => Boolean(state.token),
  },

  actions: {
    hydrate(token: string | null) {
      this.token = token
      return this.token
    },

    setToken(token: string | null) {
      this.token = token
    },

    async fetchMe() {
      const { apiFetch } = useApi()

      try {
        this.user = await apiFetch<CurrentUser>('/auth/me', { method: 'GET' })
        console.log('Usuario cargado desde /auth/me:', this.user)
      }
      catch (error: unknown) {
        if (error instanceof FetchError && error.statusCode === 404) {
          console.warn('/auth/me dio 404, intentando fallback a /users/me')
          this.user = await apiFetch<CurrentUser>('/users/me', { method: 'GET' })
          console.log('Usuario cargado desde /users/me:', this.user)
        }
        else {
          console.error('Error al cargar /me:', error)
          this.loaded = true
          throw error
        }
      }

      this.loaded = true
      return this.user
    },

    async bootstrap(initialToken: string | null = null) {
      this.hydrate(initialToken)

      if (!this.token) {
        this.user = null
        this.loaded = true
        return null
      }

      try {
        return await this.fetchMe()
      }
      catch (error) {
        console.error('Error real en bootstrap auth:', error)
        this.user = null
        this.token = null
        this.loaded = true
        return null
      }
    },

    logout() {
      this.user = null
      this.token = null
      this.loaded = true
    },
  },
})
