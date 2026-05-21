import { useQuery } from '@tanstack/react-query'
import { api } from '../../shared/api/client'

export const zoneKeys = {
  zones: ['zones'] as const,
}

export function useZonesQuery() {
  return useQuery({ queryKey: zoneKeys.zones, queryFn: () => api.zones() })
}

export const requestKeys = {
  mine: ['requests', 'mine'] as const,
  one: (id: string) => ['requests', id] as const,
  audit: (id: string) => ['requests', id, 'audit'] as const,
  adminQueue: ['admin', 'requests', 'pending'] as const,
}

export function useMyRequestsQuery() {
  return useQuery({ queryKey: requestKeys.mine, queryFn: () => api.myRequests() })
}

export function useRequestQuery(id: string | undefined) {
  return useQuery({
    queryKey: requestKeys.one(id ?? ''),
    queryFn: () => api.getRequest(id!),
    enabled: Boolean(id),
  })
}

export function useAuditQuery(id: string | undefined) {
  return useQuery({
    queryKey: requestKeys.audit(id ?? ''),
    queryFn: () => api.audit(id!),
    enabled: Boolean(id),
  })
}

export function useAdminQueueQuery(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: requestKeys.adminQueue,
    queryFn: () => api.adminQueue(),
    ...options,
  })
}
