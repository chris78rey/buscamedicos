export type ProfessionalMePayload = {
  public_display_name?: string
}

export type ProfessionalPublicProfilePayload = {
  public_title: string
  public_bio?: string | null
  consultation_price?: number | null
  province?: string | null
  city?: string | null
  sector?: string | null
  years_experience?: number | null
  languages_json?: string | null
  is_public: boolean
}

export type ProfessionalPublicProfileResponse = {
  id?: string
  professional_id: string
  public_display_name?: string | null
  public_title?: string | null
  public_bio?: string | null
  consultation_price?: number | null
  province?: string | null
  city?: string | null
  sector?: string | null
  years_experience?: number | null
  languages_json?: string | null
  is_public?: boolean
  professional_status?: string | null
  onboarding_status?: string | null
}

export type ProfessionalAvailabilityPayload = {
  weekday: number
  start_time: string
  end_time: string
  slot_minutes: number
  modality_code: string
}

export type ProfessionalAvailabilityItem = ProfessionalAvailabilityPayload & {
  id: string
  professional_id: string
  status: string
  created_at?: string | null
  updated_at?: string | null
}

export type ProfessionalTimeBlockPayload = {
  starts_at: string
  ends_at: string
  reason?: string | null
  block_type: string
}

export type ProfessionalTimeBlockItem = {
  id: string
  professional_id: string
  starts_at: string
  ends_at: string
  reason?: string | null
  block_type: string
  created_at?: string | null
  updated_at?: string | null
}

export type ProfessionalModalityItem = {
  id: string
  code: string
  name: string
}

export function useProfessionalAgenda() {
  const { apiFetch } = useApi()

  async function getProfessionalMe() {
    return await apiFetch<{ id: string; public_display_name?: string | null }>('/professionals/me', {
      method: 'GET',
    })
  }

  async function updateProfessionalMe(payload: ProfessionalMePayload) {
    return await apiFetch('/professionals/me', {
      method: 'PATCH',
      body: payload,
    })
  }

  async function getMyPublicProfile() {
    return await apiFetch<ProfessionalPublicProfileResponse>('/professionals/me/public-profile', {
      method: 'GET',
    })
  }

  async function updateMyPublicProfile(payload: ProfessionalPublicProfilePayload) {
    return await apiFetch<ProfessionalPublicProfileResponse>('/professionals/me/public-profile', {
      method: 'PUT',
      body: payload,
    })
  }

  async function getMyAvailabilities() {
    return await apiFetch<ProfessionalAvailabilityItem[]>('/professionals/me/availabilities', {
      method: 'GET',
    })
  }

  async function createAvailability(payload: ProfessionalAvailabilityPayload) {
    return await apiFetch<ProfessionalAvailabilityItem>('/professionals/me/availabilities', {
      method: 'POST',
      body: payload,
    })
  }

  async function updateAvailability(id: string, payload: ProfessionalAvailabilityPayload) {
    return await apiFetch<ProfessionalAvailabilityItem>(`/professionals/me/availabilities/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: payload,
    })
  }

  async function deleteAvailability(id: string) {
    return await apiFetch<{ status: string; id: string }>(`/professionals/me/availabilities/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    })
  }

  async function getMyTimeBlocks() {
    return await apiFetch<ProfessionalTimeBlockItem[]>('/professionals/me/time-blocks', {
      method: 'GET',
    })
  }

  async function createTimeBlock(payload: ProfessionalTimeBlockPayload) {
    return await apiFetch<ProfessionalTimeBlockItem>('/professionals/me/time-blocks', {
      method: 'POST',
      body: payload,
    })
  }

  async function updateTimeBlock(id: string, payload: ProfessionalTimeBlockPayload) {
    return await apiFetch<ProfessionalTimeBlockItem>(`/professionals/me/time-blocks/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: payload,
    })
  }

  async function deleteTimeBlock(id: string) {
    return await apiFetch<{ status: string; id: string }>(`/professionals/me/time-blocks/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    })
  }

  async function getMyModalities() {
    return await apiFetch<ProfessionalModalityItem[]>('/professionals/me/modalities', {
      method: 'GET',
    })
  }

  return {
    getProfessionalMe,
    updateProfessionalMe,
    getMyPublicProfile,
    updateMyPublicProfile,
    getMyAvailabilities,
    createAvailability,
    updateAvailability,
    deleteAvailability,
    getMyTimeBlocks,
    createTimeBlock,
    updateTimeBlock,
    deleteTimeBlock,
    getMyModalities,
  }
}
