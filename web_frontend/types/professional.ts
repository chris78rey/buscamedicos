export type ProfessionalSpecialty =
  | string
  | {
      code?: string
      name: string
    }

export type PublicProfessionalListItem = {
  professional_id: string
  public_slug?: string | null
  public_display_name: string
  public_title: string
  specialties: ProfessionalSpecialty[]
  province?: string | null
  city?: string | null
  sector?: string | null
  modalities?: string[]
  years_experience?: number | null
  consultation_price?: number | null
  next_available_at?: string | null
}

export type PublicProfessionalDetail = {
  professional_id: string
  public_display_name: string
  public_title: string
  public_bio?: string | null
  specialties: ProfessionalSpecialty[]
  province?: string | null
  city?: string | null
  sector?: string | null
  years_experience?: number | null
  consultation_price?: number | null
  modalities?: string[]
}

export type SlotItem = {
  start: string
  end: string
  is_available: boolean
}

export type ProfessionalSearchFilters = {
  city?: string
  specialty?: string
  modality?: string
  available_date?: string
}
