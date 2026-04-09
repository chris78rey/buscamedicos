import type { RoleCode } from './auth'

declare module '#app' {
  interface PageMeta {
    roles?: RoleCode[]
  }
}

export {}
