export type ConsentCreatePayload = {
  consent_type: string
  source: string
  evidence_file_id?: string | null
  expires_at?: string | null
  notes?: string | null
}

export type ConsentResponse = {
  id: string
  patient_id: string
  consent_type: string
  status: string
  granted_at: string
  revoked_at?: string | null
  expires_at?: string | null
  source: string
  evidence_file_id?: string | null
  granted_by_user_id?: string | null
  notes?: string | null
}

export type PrivacyPolicyVersion = {
  id: string
  policy_type: string
  version_code: string
  content_markdown: string
  is_active: boolean
  published_at?: string | null
  created_at: string
}

export type PrivacyPolicyVersionCreatePayload = {
  policy_type: string
  version_code: string
  content_markdown: string
}

export type ClinicalAccessLog = {
  id: string
  actor_user_id: string
  actor_role_code: string
  patient_id?: string | null
  target_user_id?: string | null
  resource_type: string
  resource_id?: string | null
  access_mode: string
  action: string
  decision: string
  exceptional_access_request_id?: string | null
  justification?: string | null
  created_at: string
}

export type PrivacyAuditorAccessLogsResponse = {
  logs: ClinicalAccessLog[]
  count: number
}

export type ResourceAccessPolicy = {
  resource_type: string
  classification_code: string
  access_mode: string
  requires_relationship: boolean
  requires_patient_authorization: boolean
  requires_justification: boolean
  max_access_minutes?: number | null
  allow_download: boolean
  is_active: boolean
}

export type ResourceAccessPolicyUpdatePayload = {
  classification_code: string
  access_mode: string
  requires_relationship: boolean
  requires_patient_authorization: boolean
  requires_justification: boolean
  max_access_minutes?: number | null
  allow_download: boolean
}

export type RetentionPolicy = {
  id: string
  code: string
  resource_type: string
  retention_days?: number | null
  archive_after_days?: number | null
  delete_mode: string
  description?: string | null
  is_active: boolean
}

export type RetentionPolicyCreatePayload = {
  code: string
  resource_type: string
  retention_days?: number | null
  archive_after_days?: number | null
  delete_mode: string
  description?: string | null
}

export type PrivacyIncident = {
  id: string
  incident_code: string
  detected_at: string
  reported_by_user_id?: string | null
  severity: string
  incident_type: string
  description: string
  affected_resource_type?: string | null
  affected_resource_id?: string | null
  status: string
  assigned_admin_id?: string | null
  resolution_summary?: string | null
  resolved_at?: string | null
}

export type PrivacyIncidentCreatePayload = {
  incident_type: string
  severity: string
  description: string
  affected_resource_type?: string | null
  affected_resource_id?: string | null
}

export type PrivacyIncidentAssignPayload = {
  admin_id: string
}

export type PrivacyIncidentResolvePayload = {
  summary: string
}

export type PrivacyIncidentDismissPayload = {
  summary: string
}

export type ExceptionalAccessRequestCreatePayload = {
  patient_id?: string | null
  target_user_id?: string | null
  resource_type: string
  resource_id?: string | null
  scope_type: string
  justification: string
  business_basis?: string | null
  requested_minutes: number
}

export type ExceptionalAccessRequestResponse = {
  id: string
  requester_user_id: string
  requester_role_code: string
  patient_id?: string | null
  target_user_id?: string | null
  resource_type: string
  resource_id?: string | null
  scope_type: string
  justification: string
  business_basis?: string | null
  requested_minutes: number
  status: string
  requires_patient_authorization: boolean
  patient_consent_id?: string | null
  approved_by_user_id?: string | null
  approved_at?: string | null
  rejected_by_user_id?: string | null
  rejected_at?: string | null
  rejection_reason?: string | null
  starts_at?: string | null
  expires_at?: string | null
  revoked_by_user_id?: string | null
  revoked_at?: string | null
  revoke_reason?: string | null
  created_at: string
}
