import type {
  AppointmentCreatePayload,
  AppointmentCreatedResponse,
  AppointmentSummary,
} from '~/types/appointment'
import type {
  ConsentCreatePayload,
  ConsentResponse,
  ClinicalAccessLog,
  ExceptionalAccessRequestCreatePayload,
  ExceptionalAccessRequestResponse,
  PrivacyAuditorAccessLogsResponse,
  PrivacyPolicyVersion,
} from '~/types/privacy'
import type {
  ProfessionalSearchFilters,
  PublicProfessionalDetail,
  PublicProfessionalListItem,
  SlotItem,
} from '~/types/professional'

type ApiFetchOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  headers?: HeadersInit
  body?: unknown
}

type AuditorLogFilters = {
  actor_user_id?: string
  patient_id?: string
  resource_type?: string
  from_date?: string
  to_date?: string
  limit?: number
}

function normalizeHeaders(headers?: HeadersInit): Record<string, string> {
  if (!headers) {
    return {}
  }

  const resolvedHeaders = new Headers(headers)
  return Object.fromEntries(resolvedHeaders.entries())
}

function cleanQuery(params: Record<string, unknown>) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => {
      if (value === null || value === undefined) {
        return false
      }

      if (typeof value === 'string') {
        return value.trim().length > 0
      }

      return true
    }),
  )
}

export function useApi() {
  const config = useRuntimeConfig()
  const token = useCookie<string | null>('access_token')

  async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
    const isFormData = options.body instanceof FormData
    
    const headers: Record<string, string> = {
      ...normalizeHeaders(options.headers),
    }

    // Si es FormData, dejamos que el navegador ponga el Content-Type con el boundary
    if (!isFormData) {
      headers['Content-Type'] = 'application/json'
    }

    if (token.value) {
      headers.Authorization = `Bearer ${token.value}`
    }

    return await $fetch<T>(`${config.public.apiBase}${path}`, {
      method: options.method,
      headers,
      body: options.body,
    })
  }

  // --- PUBLIC ---

  async function searchProfessionals(
    filters: ProfessionalSearchFilters = {},
  ): Promise<PublicProfessionalListItem[]> {
    const query = cleanQuery({
      city: filters.city,
      specialty: filters.specialty,
      modality: filters.modality,
      available_date: filters.available_date,
    })

    const queryString = new URLSearchParams(query as Record<string, string>).toString()
    const path = queryString ? `/public/professionals?${queryString}` : '/public/professionals'

    return await apiFetch<PublicProfessionalListItem[]>(path, { method: 'GET' })
  }

  async function getPublicProfessional(identifier: string): Promise<PublicProfessionalDetail> {
    return await apiFetch<PublicProfessionalDetail>(
      `/public/professionals/${encodeURIComponent(identifier)}`,
      { method: 'GET' },
    )
  }

  async function getSlots(
    professionalId: string,
    date: string,
    modality: string,
  ): Promise<SlotItem[]> {
    const query = new URLSearchParams({
      date,
      modality,
    }).toString()

    return await apiFetch<SlotItem[]>(
      `/public/professionals/${encodeURIComponent(professionalId)}/slots?${query}`,
      { method: 'GET' },
    )
  }

  // --- PATIENT ---

  async function createAppointment(
    payload: AppointmentCreatePayload,
  ): Promise<AppointmentCreatedResponse> {
    return await apiFetch<AppointmentCreatedResponse>('/patient/appointments', {
      method: 'POST',
      body: payload,
    })
  }

  async function getMyAppointments(): Promise<AppointmentSummary[]> {
    return await apiFetch<AppointmentSummary[]>('/patient/appointments', {
      method: 'GET',
    })
  }

  async function getPatientConsents(): Promise<ConsentResponse[]> {
    return await apiFetch<ConsentResponse[]>('/patient/privacy/consents', {
      method: 'GET',
    })
  }

  async function createPatientConsent(payload: ConsentCreatePayload): Promise<ConsentResponse> {
    return await apiFetch<ConsentResponse>('/patient/privacy/consents', {
      method: 'POST',
      body: payload,
    })
  }

  async function revokePatientConsent(consentId: string): Promise<ConsentResponse> {
    return await apiFetch<ConsentResponse>(`/patient/privacy/consents/${encodeURIComponent(consentId)}/revoke`, {
      method: 'POST',
    })
  }

  async function getPatientPrivacyPolicies(): Promise<PrivacyPolicyVersion[]> {
    return await apiFetch<PrivacyPolicyVersion[]>('/patient/privacy/policies/active', {
      method: 'GET',
    })
  }

  async function getPatientAccessLogs(): Promise<ClinicalAccessLog[]> {
    return await apiFetch<ClinicalAccessLog[]>('/patient/privacy/access-log/me', {
      method: 'GET',
    })
  }

  // --- PROFESSIONAL ---

  async function getProfessionalMe(): Promise<any> {
    return await apiFetch<any>('/professionals/me', { method: 'GET' })
  }

  async function updateProfessionalMe(payload: any): Promise<any> {
    return await apiFetch<any>('/professionals/me', {
      method: 'PATCH',
      body: payload,
    })
  }

  async function getProfessionalVerificationStatus(): Promise<any> {
    return await apiFetch<any>('/professionals/me/verification-status', { method: 'GET' })
  }

  async function uploadProfessionalDocument(formData: FormData): Promise<any> {
    return await apiFetch<any>('/professionals/me/documents', {
      method: 'POST',
      body: formData,
    })
  }

  async function deleteProfessionalDocument(documentId: string): Promise<any> {
    return await apiFetch<any>(`/professionals/me/documents/${encodeURIComponent(documentId)}`, {
      method: 'DELETE',
    })
  }

  async function submitProfessionalVerification(): Promise<any> {
    return await apiFetch<any>('/professionals/me/submit-verification', { method: 'POST' })
  }

  async function createExceptionalAccessRequest(
    payload: ExceptionalAccessRequestCreatePayload,
  ): Promise<ExceptionalAccessRequestResponse> {
    return await apiFetch<ExceptionalAccessRequestResponse>('/professionals/me/privacy/exceptional-access-requests', {
      method: 'POST',
      body: payload,
    })
  }

  async function getProfessionalExceptionalAccessRequests(): Promise<ExceptionalAccessRequestResponse[]> {
    return await apiFetch<ExceptionalAccessRequestResponse[]>('/professionals/me/privacy/exceptional-access-requests', {
      method: 'GET',
    })
  }

  async function getProfessionalAccessLogs(): Promise<ClinicalAccessLog[]> {
    return await apiFetch<ClinicalAccessLog[]>('/professionals/me/privacy/access-log/me', {
      method: 'GET',
    })
  }

  // --- PRIVACY AUDITOR ---

  async function getPrivacyAuditorAccessLogs(
    filters: AuditorLogFilters = {},
  ): Promise<PrivacyAuditorAccessLogsResponse> {
    const query = cleanQuery({
      actor_user_id: filters.actor_user_id,
      patient_id: filters.patient_id,
      resource_type: filters.resource_type,
      from_date: filters.from_date,
      to_date: filters.to_date,
      limit: filters.limit,
    })

    const queryString = new URLSearchParams(
      Object.entries(query).reduce<Record<string, string>>((acc, [key, value]) => {
        acc[key] = String(value)
        return acc
      }, {}),
    ).toString()

    const path = queryString ? `/privacy-auditor/access-logs?${queryString}` : '/privacy-auditor/access-logs'

    return await apiFetch<PrivacyAuditorAccessLogsResponse>(path, {
      method: 'GET',
    })
  }

  return {
    apiFetch,
    searchProfessionals,
    getPublicProfessional,
    getSlots,
    createAppointment,
    getMyAppointments,
    getPatientConsents,
    createPatientConsent,
    revokePatientConsent,
    getPatientPrivacyPolicies,
    getPatientAccessLogs,
    getProfessionalMe,
    updateProfessionalMe,
    getProfessionalVerificationStatus,
    uploadProfessionalDocument,
    deleteProfessionalDocument,
    submitProfessionalVerification,
    createExceptionalAccessRequest,
    getProfessionalExceptionalAccessRequests,
    getProfessionalAccessLogs,
    getPrivacyAuditorAccessLogs,
  }
}
