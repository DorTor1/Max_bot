import type { components } from '../shared/api/schema'
import zonesFixture from './fixtures/zones.json'

export type User = components['schemas']['User']
export type Request = components['schemas']['Request']
export type AuditEvent = components['schemas']['AuditEvent']
export type RequestStatus = components['schemas']['RequestStatus']
export type Role = components['schemas']['Role']
export type RejectReason = components['schemas']['RejectReason']

export const CONSENT_VERSION = '2026-05-1'

const requests = new Map<string, Request>()
const auditByRequest = new Map<string, AuditEvent[]>()
let seq = 100

export function mockRole(): Role {
  const r = import.meta.env.VITE_MOCK_ROLE
  if (r === 'admin' || r === 'tech_admin') return r
  return 'initiator'
}

let currentUser: User = {
  id: import.meta.env.VITE_MOCK_USER_ID || 'user-demo-1',
  displayName: import.meta.env.VITE_MOCK_USER_NAME || 'Иван Инициатор',
}

let consentAccepted = false

export function getZones(): { id: string; title: string }[] {
  return zonesFixture as { id: string; title: string }[]
}

function newId(): string {
  return crypto.randomUUID()
}

function nextNumber(): string {
  seq += 1
  const y = new Date().getFullYear()
  return `GP-${y}-${String(seq).padStart(6, '0')}`
}

/** Следующий человекочитаемый номер заявки (GP-YYYY-NNNNNN) */
export function allocateNumber(): string {
  return nextNumber()
}

export function zoneTitle(zoneId: string): string {
  const z = getZones().find((x) => x.id === zoneId)
  return z?.title ?? zoneId
}

export function getSessionResponse(): components['schemas']['Session'] {
  return {
    user: currentUser,
    role: mockRole(),
    consent: { required: !consentAccepted, version: CONSENT_VERSION },
  }
}

export function setSessionUser(u: User) {
  currentUser = u
}

export function setConsentAccepted() {
  consentAccepted = true
}

export function pushAudit(ev: AuditEvent) {
  const list = auditByRequest.get(ev.requestId) ?? []
  list.push(ev)
  auditByRequest.set(ev.requestId, list)
}

export function listAudit(requestId: string): AuditEvent[] {
  return [...(auditByRequest.get(requestId) ?? [])].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  )
}

export function getRequest(id: string): Request | undefined {
  return requests.get(id)
}

export function saveRequest(r: Request) {
  requests.set(r.id, r)
}

export function allRequests(): Request[] {
  return [...requests.values()]
}

export function canAccessRequest(r: Request, role: Role): boolean {
  if (role === 'admin' || role === 'tech_admin') return true
  return r.initiator.id === currentUser.id
}

export function seedIfEmpty() {
  if (requests.size > 0) return

  const mk = (
    id: string,
    initiator: User,
    guest: string,
    status: RequestStatus,
    clarification?: { question: string; answer?: string },
  ): Request => {
    const zoneId = 'main'
    const now = new Date().toISOString()
    return {
      id,
      number: nextNumber(),
      guestFullName: guest,
      visitDate: '2026-05-22',
      visitTime: 'morning',
      zoneId,
      zone: zoneTitle(zoneId),
      purpose: 'Демо-заявка из моков',
      status,
      initiator: { id: initiator.id, displayName: initiator.displayName },
      clarification,
      createdAt: now,
      updatedAt: now,
    }
  }

  const id1 = newId()
  const id2 = newId()
  const colleague: User = { id: 'user-colleague-2', displayName: 'Петр Коллега' }

  const r1 = mk(id1, colleague, 'Петрова Анна Сергеевна', 'pending')
  const r2 = mk(id2, currentUser, 'Сидоров Илья Олегович', 'clarification', {
    question: 'Уточните, пожалуйста, кабинет визита.',
  })

  saveRequest(r1)
  saveRequest(r2)

  const t1 = new Date().toISOString()
  pushAudit({
    id: newId(),
    requestId: id1,
    type: 'submitted',
    actorId: colleague.id,
    actorName: colleague.displayName,
    payload: { number: r1.number },
    createdAt: t1,
  })
  pushAudit({
    id: newId(),
    requestId: id2,
    type: 'submitted',
    actorId: currentUser.id,
    actorName: currentUser.displayName,
    payload: { number: r2.number },
    createdAt: t1,
  })
  pushAudit({
    id: newId(),
    requestId: id2,
    type: 'clarification_requested',
    actorId: 'admin-mock',
    actorName: 'ИБ (мок)',
    payload: { preview: 'Уточните кабинет' },
    createdAt: t1,
  })
}
