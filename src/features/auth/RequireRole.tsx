import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import type { components } from '../../shared/api/schema'
import { useSessionQuery } from './session'

type Role = components['schemas']['Role']

export function RequireRole({
  role,
  children,
}: {
  role: Role | Role[]
  children: ReactNode
}) {
  const { data, isPending } = useSessionQuery()
  if (isPending || !data) return null
  const allowed = Array.isArray(role) ? role : [role]
  if (!allowed.includes(data.role)) {
    return <Navigate to="/" replace />
  }
  return children
}
