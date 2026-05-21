import type { components } from './schema'

export type ApiErrorBody = components['schemas']['Error']
export type Session = components['schemas']['Session']
export type Request = components['schemas']['Request']
export type Zone = components['schemas']['Zone']
export type AuditEvent = components['schemas']['AuditEvent']
export type RejectReason = components['schemas']['RejectReason']
export type CreateRequestBody = components['schemas']['CreateRequestBody']

export class ApiError extends Error {
  readonly status: number
  readonly body: ApiErrorBody | null

  constructor(status: number, body: ApiErrorBody | null) {
    super(body?.message ?? `Ошибка ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

function baseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? ''
}

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let body: ApiErrorBody | null = null
    try {
      body = (await res.json()) as ApiErrorBody
    } catch {
      /* empty */
    }
    throw new ApiError(res.status, body)
  }
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${baseUrl()}${path}`, {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  return parseJson<T>(res)
}

export const api = {
  health: () => req<{ status: string }>('GET', '/health'),
  authSession: (payload: { user: components['schemas']['User'] }) =>
    req<Session>('POST', '/auth/session', payload),
  postConsent: (payload: { version: string }) => req<void>('POST', '/consent', payload),
  zones: () => req<Zone[]>('GET', '/zones'),
  myRequests: () => req<Request[]>('GET', '/requests?mine=true'),
  createRequest: (payload: CreateRequestBody) => req<Request>('POST', '/requests', payload),
  getRequest: (id: string) => req<Request>('GET', `/requests/${id}`),
  cancelRequest: (id: string) => req<Request>('POST', `/requests/${id}/cancel`),
  answerClarification: (id: string, payload: { answer: string }) =>
    req<Request>('POST', `/requests/${id}/clarification/answer`, payload),
  audit: (id: string) => req<AuditEvent[]>('GET', `/requests/${id}/audit`),
  adminQueue: () => req<Request[]>('GET', '/admin/requests?status=pending'),
  adminApprove: (id: string, payload?: { comment?: string }) =>
    req<Request>('POST', `/admin/requests/${id}/approve`, payload ?? {}),
  adminReject: (id: string, payload: { reasonCode: RejectReason; comment?: string }) =>
    req<Request>('POST', `/admin/requests/${id}/reject`, payload),
  adminClarify: (id: string, payload: { question: string }) =>
    req<Request>('POST', `/admin/requests/${id}/clarify`, payload),
  adminClose: (id: string) => req<Request>('POST', `/admin/requests/${id}/close`),
}
