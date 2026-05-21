import type { components } from '../../shared/api/schema'

export type VisitTime = components['schemas']['VisitTime']

export const VISIT_TIME_OPTIONS: { value: VisitTime; label: string }[] = [
  { value: 'morning', label: 'Утро' },
  { value: 'day', label: 'День' },
  { value: 'evening', label: 'Вечер' },
]
