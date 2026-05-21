import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api/client'
import { readMaxUser } from './maxProfile'

export const sessionKeys = {
  session: ['session'] as const,
}

export function useSessionQuery() {
  return useQuery({
    queryKey: sessionKeys.session,
    queryFn: async () => {
      const user = await readMaxUser()
      return api.authSession({ user })
    },
    staleTime: 30_000,
  })
}

export function useConsentMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (version: string) => api.postConsent({ version }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: sessionKeys.session })
    },
  })
}
