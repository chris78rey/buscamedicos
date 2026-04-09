export type RoleCode =
  | 'super_admin'
  | 'admin_validation'
  | 'admin_support'
  | 'admin_moderation'
  | 'admin_privacy'
  | 'patient'
  | 'professional'
  | 'privacy_auditor'

export type RegisterRole = 'patient' | 'professional'

export type UserRole = {
  code: RoleCode
}

export type CurrentUser = {
  id: string
  email: string
  status?: string
  is_email_verified?: boolean
  role_codes?: RoleCode[]
  primary_role?: RoleCode | null
  actor_type?: 'admin' | 'patient' | 'professional' | 'unknown'
  roles?: UserRole[]
}

export type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: string
}

export type LoginPayload = {
  email: string
  password: string
}

export type RegisterPayload = {
  first_name: string
  last_name: string
  email: string
  password: string
  national_id: string
  phone: string
}

export type ProfessionalRegisterPayload = RegisterPayload & {
  professional_type: string
}
