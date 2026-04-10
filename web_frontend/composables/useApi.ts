import type {
  AppointmentCreatePayload,
  AppointmentCreatedResponse,
  AppointmentSummary,
  CheckoutResponse,
  PaymentIntentResponse,
  PaymentIntentConfirmResponse,
  PaymentResponse,
} from '~/types/appointment'
import type {
  ClinicalAccessLog,
  ConsentCreatePayload,
  ConsentResponse,
  ExceptionalAccessRequestCreatePayload,
  ExceptionalAccessRequestResponse,
  PrivacyAuditorAccessLogsResponse,
  PrivacyIncident,
  PrivacyIncidentAssignPayload,
  PrivacyIncidentCreatePayload,
  PrivacyIncidentDismissPayload,
  PrivacyIncidentResolvePayload,
  PrivacyPolicyVersion,
  PrivacyPolicyVersionCreatePayload,
  ResourceAccessPolicy,
  ResourceAccessPolicyUpdatePayload,
  RetentionPolicy,
  RetentionPolicyCreatePayload,
} from '~/types/privacy'
import type {
  ProfessionalSearchFilters,
  PublicProfessionalDetail,
  PublicProfessionalListItem,
  SlotItem,
} from '~/types/professional'
import type {
  AdminVerificationRequest,
  AdminVerificationRequestDetail,
} from '~/types/verification'

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

type AdminPrivacyLogFilters = {
  actor_user_id?: string
  resource_type?: string
  from_date?: string
  to_date?: string
}

type AdminIncidentFilters = {
  status_filter?: string
  severity?: string
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

function buildQueryString(params: Record<string, unknown>) {
  const query = cleanQuery(params)
  return new URLSearchParams(
    Object.entries(query).reduce<Record<string, string>>((acc, [key, value]) => {
      acc[key] = String(value)
      return acc
    }, {}),
  ).toString()
}

export function useApi() {
  const config = useRuntimeConfig()
  const token = useCookie<string | null>('access_token')

  async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
    const isFormData = options.body instanceof FormData
    const baseHeaders: Record<string, string> = isFormData ? {} : { 'Content-Type': 'application/json' }

    const headers: Record<string, string> = {
      ...baseHeaders,
      ...normalizeHeaders(options.headers),
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

  // Professional Me & Documents
  async function getProfessionalMe(): Promise<any> {
    return await apiFetch('/professionals/me', { method: 'GET' })
  }

  async function updateProfessionalMe(payload: any): Promise<any> {
    return await apiFetch('/professionals/me', {
      method: 'PATCH',
      body: payload,
    })
  }

  async function getProfessionalVerificationStatus(): Promise<any> {
    return await apiFetch('/professionals/me/verification-status', { method: 'GET' })
  }

  async function uploadProfessionalDocument(formData: FormData): Promise<any> {
    return await apiFetch('/professionals/me/documents', {
      method: 'POST',
      body: formData,
    })
  }

  async function deleteProfessionalDocument(documentId: string): Promise<any> {
    return await apiFetch(`/professionals/me/documents/${encodeURIComponent(documentId)}`, {
      method: 'DELETE',
    })
  }

  async function submitProfessionalVerification(): Promise<any> {
    return await apiFetch('/professionals/me/submit-verification', {
      method: 'POST',
    })
  }

  async function searchProfessionals(
    filters: ProfessionalSearchFilters = {},
  ): Promise<PublicProfessionalListItem[]> {
    const queryString = buildQueryString({
      city: filters.city,
      specialty: filters.specialty,
      modality: filters.modality,
      available_date: filters.available_date,
    })

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

  async function getCheckout(appointmentId: string): Promise<CheckoutResponse> {
    return await apiFetch<CheckoutResponse>(`/patient/appointments/${encodeURIComponent(appointmentId)}/checkout`, {
      method: 'GET',
    })
  }

  async function createPaymentIntent(
    appointmentId: string,
    idempotencyKey: string,
  ): Promise<PaymentIntentResponse> {
    return await apiFetch<PaymentIntentResponse>(
      `/patient/appointments/${encodeURIComponent(appointmentId)}/payment-intent`,
      {
        method: 'POST',
        body: { idempotency_key: idempotencyKey },
      },
    )
  }

  async function confirmSandboxPayment(intentId: string): Promise<PaymentIntentConfirmResponse> {
    return await apiFetch<PaymentIntentConfirmResponse>(
      `/patient/payment-intents/${encodeURIComponent(intentId)}/confirm-sandbox`,
      { method: 'POST' },
    )
  }

  async function failSandboxPayment(intentId: string): Promise<{ status: string }> {
    return await apiFetch<{ status: string }>(
      `/patient/payment-intents/${encodeURIComponent(intentId)}/fail-sandbox`,
      { method: 'POST' },
    )
  }

  async function getMyPayments(): Promise<PaymentResponse[]> {
    return await apiFetch<PaymentResponse[]>('/patient/payments', {
      method: 'GET',
    })
  }

  async function getMyPayment(paymentId: string): Promise<PaymentResponse> {
    return await apiFetch<PaymentResponse>(`/patient/payments/${encodeURIComponent(paymentId)}`, {
      method: 'GET',
    })
  }

  // Professional endpoints
  async function getMyPrices(): Promise<{ id: string; modality_code: string; amount: number; currency_code: string; is_active: boolean }[]> {
    return await apiFetch('/professionals/me/prices', { method: 'GET' })
  }

  async function updateMyPrice(
    modalityCode: string,
    amount: number,
  ): Promise<{ id: string; modality_code: string; amount: number; currency_code: string; is_active: boolean }> {
    return await apiFetch('/professionals/me/prices', {
      method: 'PUT',
      body: { modality_code: modalityCode, amount },
    })
  }

  async function getPendingEarnings(): Promise<{
    total_pending_gross: number
    total_pending_commission: number
    total_pending_net: number
    currency_code: string
    appointments_count: number
  }> {
    return await apiFetch('/professionals/me/earnings/pending', { method: 'GET' })
  }

  async function getMySettlements(): Promise<{
    id: string
    batch_code: string
    total_gross: number
    total_commission: number
    total_net: number
    currency_code: string
    status: string
    generated_at?: string | null
    paid_at?: string | null
  }[]> {
    return await apiFetch('/professionals/me/earnings/settlements', { method: 'GET' })
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
  
  async function getProfessionalAppointments(): Promise<AppointmentSummary[]> {
    return await apiFetch<AppointmentSummary[]>('/professionals/me/appointments', {
      method: 'GET',
    })
  }

  async function confirmAppointment(appointmentId: string): Promise<AppointmentSummary> {
    return await apiFetch<AppointmentSummary>(`/professionals/me/appointments/${encodeURIComponent(appointmentId)}/confirm`, {
      method: 'POST',
    })
  }

  async function cancelAppointment(appointmentId: string, reason?: string): Promise<AppointmentSummary> {
    return await apiFetch<AppointmentSummary>(`/professionals/me/appointments/${encodeURIComponent(appointmentId)}/cancel`, {
      method: 'POST',
      body: reason ? { reason } : undefined,
    })
  }

  async function completeAppointment(appointmentId: string): Promise<AppointmentSummary> {
    return await apiFetch<AppointmentSummary>(`/professionals/me/appointments/${encodeURIComponent(appointmentId)}/complete`, {
      method: 'POST',
    })
  }

  async function getPrivacyAuditorAccessLogs(
    filters: AuditorLogFilters = {},
  ): Promise<PrivacyAuditorAccessLogsResponse> {
    const queryString = buildQueryString({
      actor_user_id: filters.actor_user_id,
      patient_id: filters.patient_id,
      resource_type: filters.resource_type,
      from_date: filters.from_date,
      to_date: filters.to_date,
      limit: filters.limit,
    })

    const path = queryString ? `/privacy-auditor/access-logs?${queryString}` : '/privacy-auditor/access-logs'
    return await apiFetch<PrivacyAuditorAccessLogsResponse>(path, {
      method: 'GET',
    })
  }

  async function getAdminPrivacyPolicies(policyType?: string): Promise<PrivacyPolicyVersion[]> {
    const queryString = buildQueryString({
      policy_type: policyType,
    })

    const path = queryString ? `/admin/privacy/policies?${queryString}` : '/admin/privacy/policies'
    return await apiFetch<PrivacyPolicyVersion[]>(path, {
      method: 'GET',
    })
  }

  async function createAdminPrivacyPolicy(
    payload: PrivacyPolicyVersionCreatePayload,
  ): Promise<PrivacyPolicyVersion> {
    return await apiFetch<PrivacyPolicyVersion>('/admin/privacy/policies', {
      method: 'POST',
      body: payload,
    })
  }

  async function publishAdminPrivacyPolicy(policyId: string): Promise<PrivacyPolicyVersion> {
    return await apiFetch<PrivacyPolicyVersion>(`/admin/privacy/policies/${encodeURIComponent(policyId)}/publish`, {
      method: 'POST',
    })
  }

  async function getAdminPrivacyResourcePolicies(): Promise<ResourceAccessPolicy[]> {
    return await apiFetch<ResourceAccessPolicy[]>('/admin/privacy/resource-policies', {
      method: 'GET',
    })
  }

  async function updateAdminPrivacyResourcePolicy(
    resourceType: string,
    payload: ResourceAccessPolicyUpdatePayload,
  ): Promise<ResourceAccessPolicy> {
    return await apiFetch<ResourceAccessPolicy>(`/admin/privacy/resource-policies/${encodeURIComponent(resourceType)}`, {
      method: 'PUT',
      body: payload,
    })
  }

  async function getAdminPrivacyAccessLogs(
    filters: AdminPrivacyLogFilters = {},
  ): Promise<ClinicalAccessLog[]> {
    const queryString = buildQueryString({
      actor_user_id: filters.actor_user_id,
      resource_type: filters.resource_type,
      from_date: filters.from_date,
      to_date: filters.to_date,
    })

    const path = queryString ? `/admin/privacy/access-logs?${queryString}` : '/admin/privacy/access-logs'
    return await apiFetch<ClinicalAccessLog[]>(path, {
      method: 'GET',
    })
  }

  async function exportAdminPrivacyAccessLogsMeta(
    filters: AdminPrivacyLogFilters = {},
  ): Promise<ClinicalAccessLog[]> {
    const queryString = buildQueryString({
      actor_user_id: filters.actor_user_id,
      resource_type: filters.resource_type,
      from_date: filters.from_date,
      to_date: filters.to_date,
    })

    const path = queryString
      ? `/admin/privacy/access-logs/export-meta?${queryString}`
      : '/admin/privacy/access-logs/export-meta'

    return await apiFetch<ClinicalAccessLog[]>(path, {
      method: 'GET',
    })
  }

  async function getAdminPrivacyRetentionPolicies(): Promise<RetentionPolicy[]> {
    return await apiFetch<RetentionPolicy[]>('/admin/privacy/retention-policies', {
      method: 'GET',
    })
  }

  async function createAdminPrivacyRetentionPolicy(
    payload: RetentionPolicyCreatePayload,
  ): Promise<RetentionPolicy> {
    return await apiFetch<RetentionPolicy>('/admin/privacy/retention-policies', {
      method: 'POST',
      body: payload,
    })
  }

  async function updateAdminPrivacyRetentionPolicy(
    policyId: string,
    payload: RetentionPolicyCreatePayload,
  ): Promise<RetentionPolicy> {
    return await apiFetch<RetentionPolicy>(`/admin/privacy/retention-policies/${encodeURIComponent(policyId)}`, {
      method: 'PUT',
      body: payload,
    })
  }

  async function getAdminPrivacyIncidents(
    filters: AdminIncidentFilters = {},
  ): Promise<PrivacyIncident[]> {
    const queryString = buildQueryString({
      status_filter: filters.status_filter,
      severity: filters.severity,
    })

    const path = queryString ? `/admin/privacy/incidents?${queryString}` : '/admin/privacy/incidents'
    return await apiFetch<PrivacyIncident[]>(path, {
      method: 'GET',
    })
  }

  async function createAdminPrivacyIncident(
    payload: PrivacyIncidentCreatePayload,
  ): Promise<PrivacyIncident> {
    return await apiFetch<PrivacyIncident>('/admin/privacy/incidents', {
      method: 'POST',
      body: payload,
    })
  }

  async function assignAdminPrivacyIncident(
    incidentId: string,
    payload: PrivacyIncidentAssignPayload,
  ): Promise<PrivacyIncident> {
    return await apiFetch<PrivacyIncident>(`/admin/privacy/incidents/${encodeURIComponent(incidentId)}/assign`, {
      method: 'POST',
      body: payload,
    })
  }

  async function containAdminPrivacyIncident(
    incidentId: string,
  ): Promise<PrivacyIncident> {
    return await apiFetch<PrivacyIncident>(`/admin/privacy/incidents/${encodeURIComponent(incidentId)}/contain`, {
      method: 'POST',
    })
  }

  async function resolveAdminPrivacyIncident(
    incidentId: string,
    payload: PrivacyIncidentResolvePayload,
  ): Promise<PrivacyIncident> {
    return await apiFetch<PrivacyIncident>(`/admin/privacy/incidents/${encodeURIComponent(incidentId)}/resolve`, {
      method: 'POST',
      body: payload,
    })
  }

  async function dismissAdminPrivacyIncident(
    incidentId: string,
    payload: PrivacyIncidentDismissPayload,
  ): Promise<PrivacyIncident> {
    return await apiFetch<PrivacyIncident>(`/admin/privacy/incidents/${encodeURIComponent(incidentId)}/dismiss`, {
      method: 'POST',
      body: payload,
    })
  }

  // Admin verification endpoints
  async function getAdminVerificationRequests(): Promise<AdminVerificationRequest[]> {
    return await apiFetch<AdminVerificationRequest[]>('/admin/verification-requests', { method: 'GET' })
  }

  async function getAdminVerificationRequest(requestId: string): Promise<AdminVerificationRequestDetail> {
    return await apiFetch<AdminVerificationRequestDetail>(`/admin/verification-requests/${encodeURIComponent(requestId)}`, { method: 'GET' })
  }

  async function assignAdminVerificationRequest(requestId: string): Promise<{ status: string; admin_id: string }> {
    return await apiFetch<{ status: string; admin_id: string }>(`/admin/verification-requests/${encodeURIComponent(requestId)}/assign`, { method: 'POST' })
  }

  async function approveAdminVerificationDocument(
    requestId: string,
    documentId: string,
    notes?: string,
  ): Promise<{ status: string; document_id: string }> {
    return await apiFetch<{ status: string; document_id: string }>(
      `/admin/verification-requests/${encodeURIComponent(requestId)}/documents/${encodeURIComponent(documentId)}/approve`,
      { method: 'POST', body: notes ? { notes } : undefined },
    )
  }

  async function rejectAdminVerificationDocument(
    requestId: string,
    documentId: string,
    reason: string,
  ): Promise<{ status: string; document_id: string; reason: string }> {
    return await apiFetch<{ status: string; document_id: string; reason: string }>(
      `/admin/verification-requests/${encodeURIComponent(requestId)}/documents/${encodeURIComponent(documentId)}/reject`,
      { method: 'POST', body: { reason } },
    )
  }

  async function approveAdminVerification(requestId: string): Promise<{ status: string; professional_status: string }> {
    return await apiFetch<{ status: string; professional_status: string }>(
      `/admin/verification-requests/${encodeURIComponent(requestId)}/approve`,
      { method: 'POST' },
    )
  }

  async function rejectAdminVerification(
    requestId: string,
    reason: string,
  ): Promise<{ status: string; reason: string }> {
    return await apiFetch<{ status: string; reason: string }>(
      `/admin/verification-requests/${encodeURIComponent(requestId)}/reject`,
      { method: 'POST', body: { reason } },
    )
  }

  async function requestCorrectionAdminVerification(
    requestId: string,
    reason: string,
  ): Promise<{ status: string; reason: string }> {
    return await apiFetch<{ status: string; reason: string }>(
      `/admin/verification-requests/${encodeURIComponent(requestId)}/request-correction`,
      { method: 'POST', body: { reason } },
    )
  }

  return {
    apiFetch,
    searchProfessionals,
    getAdminVerificationRequests,
    getAdminVerificationRequest,
    assignAdminVerificationRequest,
    approveAdminVerificationDocument,
    rejectAdminVerificationDocument,
    approveAdminVerification,
    rejectAdminVerification,
    requestCorrectionAdminVerification,
    getPublicProfessional,
    getSlots,
    createAppointment,
    getMyAppointments,
    getCheckout,
    createPaymentIntent,
    confirmSandboxPayment,
    failSandboxPayment,
    getMyPayments,
    getMyPayment,
    getMyPrices,
    updateMyPrice,
    getPendingEarnings,
    getMySettlements,
    getPatientConsents,
    createPatientConsent,
    revokePatientConsent,
    getPatientPrivacyPolicies,
    getPatientAccessLogs,
    createExceptionalAccessRequest,
    getProfessionalExceptionalAccessRequests,
    getProfessionalAccessLogs,
    getProfessionalAppointments,
    confirmAppointment,
    cancelAppointment,
    completeAppointment,
    getProfessionalMe,
    updateProfessionalMe,
    getProfessionalVerificationStatus,
    uploadProfessionalDocument,
    deleteProfessionalDocument,
    submitProfessionalVerification,
    getPrivacyAuditorAccessLogs,
    getAdminPrivacyPolicies,
    createAdminPrivacyPolicy,
    publishAdminPrivacyPolicy,
    getAdminPrivacyResourcePolicies,
    updateAdminPrivacyResourcePolicy,
    getAdminPrivacyAccessLogs,
    exportAdminPrivacyAccessLogsMeta,
    getAdminPrivacyRetentionPolicies,
    createAdminPrivacyRetentionPolicy,
    updateAdminPrivacyRetentionPolicy,
    getAdminPrivacyIncidents,
    createAdminPrivacyIncident,
    assignAdminPrivacyIncident,
    containAdminPrivacyIncident,
    resolveAdminPrivacyIncident,
    dismissAdminPrivacyIncident,
  }
}
