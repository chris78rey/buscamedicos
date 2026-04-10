export type AdminVerificationRequest = {
  id: string
  professional_id: string
  status: string
  submitted_at: string
  assigned_admin_id: string | null
  reviewed_by: string | null
  decision_reason: string | null
  professional_display_name: string | null
  professional_email: string | null
  document_count: number
  approved_count: number
  pending_count: number
  rejected_count: number
}

export type AdminProfessionalBasicInfo = {
  id: string
  public_display_name: string | null
  professional_type: string | null
  email: string | null
}

export type AdminPersonBasicInfo = {
  id: string
  first_name: string | null
  last_name: string | null
  national_id: string | null
  phone: string | null
}

export type AdminDocumentResponse = {
  id: string
  professional_id: string
  document_type: string
  file_id: string
  original_filename: string
  mime_type: string
  sha256: string
  review_status: string
  review_notes: string | null
  uploaded_at: string
  download_url: string
}

export type AdminVerificationRequestDetail = {
  id: string
  professional_id: string
  status: string
  submitted_at: string
  assigned_admin_id: string | null
  decision_at: string | null
  decision_reason: string | null
  reviewed_by: string | null
  professional: AdminProfessionalBasicInfo | null
  person: AdminPersonBasicInfo | null
  documents: AdminDocumentResponse[]
}
