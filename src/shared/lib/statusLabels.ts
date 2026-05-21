import type { components } from '../api/schema'

export type RequestStatus = components['schemas']['RequestStatus']

const map: Record<RequestStatus, string> = {
  pending: 'На рассмотрении',
  approved: 'Одобрено',
  rejected: 'Отклонено',
  clarification: 'Нужно уточнение',
  cancelled: 'Отменено',
  closed: 'Закрыто',
}

export function requestStatusLabel(s: RequestStatus): string {
  return map[s] ?? s
}
