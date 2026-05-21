import { create } from 'zustand'
import type { components } from '../../shared/api/schema'

export type VisitTime = components['schemas']['VisitTime']

export type RequestDraft = {
  guestFullName: string
  visitDate: string
  visitTime: VisitTime | ''
  zoneId: string
  purpose: string
}

const empty: RequestDraft = {
  guestFullName: '',
  visitDate: '',
  visitTime: '',
  zoneId: '',
  purpose: '',
}

type Store = {
  draft: RequestDraft
  patch: (p: Partial<RequestDraft>) => void
  reset: () => void
}

export const useRequestDraftStore = create<Store>((set) => ({
  draft: { ...empty },
  patch: (p) => set((s) => ({ draft: { ...s.draft, ...p } })),
  reset: () => set({ draft: { ...empty } }),
}))
