export type AppointmentCreatePayload = {
  professional_id: string
  modality_code: string
  scheduled_start: string
  patient_note?: string
}

export type AppointmentCreatedResponse = {
  id: string
  public_code: string
  status: string
  scheduled_start: string
  scheduled_end: string
}

export type AppointmentSummary = {
  id: string
  public_code?: string | null
  status: string
  scheduled_start: string
  scheduled_end: string
  modality_code?: string | null
  patient_note?: string | null
  cancellation_reason?: string | null
  reschedule_reason?: string | null
  created_at?: string | null
  financial_status?: string | null
}

export type CheckoutResponse = {
  appointment_id: string
  professional_name: string
  modality_code: string
  gross_amount: number
  currency_code: string
  amount_total: number
  payment_status: string
}

export type PaymentIntentResponse = {
  id: string
  amount_total: number
  status: string
  expires_at?: string | null
}

export type PaymentIntentConfirmResponse = {
  payment_id: string
  payment_status: string
  appointment_financial_status: string
  appointment_operational_status: string
}

export type PaymentResponse = {
  id: string
  amount_total: number
  currency_code: string
  status: string
  paid_at?: string | null
  external_reference?: string | null
}
