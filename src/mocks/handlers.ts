import { http, HttpResponse } from 'msw'
import type { components } from '../shared/api/schema'
import {
  allocateNumber,
  allRequests,
  canAccessRequest,
  getRequest,
  getSessionResponse,
  getZones,
  listAudit,
  mockRole,
  pushAudit,
  saveRequest,
  seedIfEmpty,
  setConsentAccepted,
  setSessionUser,
} from './state'
import type { AuditEvent, RejectReason, Request, RequestStatus, User } from './state'

type ErrorBody = components['schemas']['Error']

function err(status: number, code: string, message: string, field?: string) {
  const body: ErrorBody = field ? { code, message, field } : { code, message }
  return HttpResponse.json(body, { status })
}

function role(): ReturnType<typeof mockRole> {
  return mockRole()
}

function touch(r: Request): Request {
  return { ...r, updatedAt: new Date().toISOString() }
}

export const handlers = [
  http.get('/health', () => HttpResponse.json({ status: 'ok' })),

  http.post('/auth/session', async ({ request }) => {
    seedIfEmpty()
    let body: { user: User }
    try {
      body = (await request.json()) as { user: User }
    } catch {
      return err(400, 'BAD_JSON', 'Некорректное тело запроса')
    }
    if (!body?.user?.id) return err(400, 'VALIDATION', 'Нужен user.id', 'user.id')
    setSessionUser(body.user)
    return HttpResponse.json(getSessionResponse())
  }),

  http.post('/consent', async ({ request }) => {
    let body: { version: string }
    try {
      body = (await request.json()) as { version: string }
    } catch {
      return err(400, 'BAD_JSON', 'Некорректное тело запроса')
    }
    if (!body?.version) return err(400, 'VALIDATION', 'Нужна version', 'version')
    setConsentAccepted()
    return new HttpResponse(null, { status: 204 })
  }),

  http.get('/zones', () => HttpResponse.json(getZones())),

  http.get('/requests', ({ request }) => {
    const url = new URL(request.url)
    if (url.searchParams.get('mine') !== 'true') {
      return err(400, 'VALIDATION', 'Ожидается mine=true', 'mine')
    }
    const uid = getSessionResponse().user.id
    const list = allRequests().filter((r) => r.initiator.id === uid)
    return HttpResponse.json(list)
  }),

  http.post('/requests', async ({ request }) => {
    let body: components['schemas']['CreateRequestBody']
    try {
      body = (await request.json()) as components['schemas']['CreateRequestBody']
    } catch {
      return err(400, 'BAD_JSON', 'Некорректное тело запроса')
    }
    const zone = getZones().find((z) => z.id === body.zoneId)
    if (!zone) return err(400, 'VALIDATION', 'Неизвестная зона', 'zoneId')

    const sess = getSessionResponse()
    const now = new Date().toISOString()
    const id = crypto.randomUUID()
    const num = allocateNumber()

    const r: Request = {
      id,
      number: num,
      guestFullName: body.guestFullName,
      visitDate: body.visitDate,
      visitTime: body.visitTime,
      zoneId: body.zoneId,
      zone: zone.title,
      purpose: body.purpose,
      status: 'pending',
      initiator: { id: sess.user.id, displayName: sess.user.displayName },
      createdAt: now,
      updatedAt: now,
    }
    saveRequest(r)
    const ev: AuditEvent = {
      id: crypto.randomUUID(),
      requestId: id,
      type: 'submitted',
      actorId: sess.user.id,
      actorName: sess.user.displayName,
      payload: { number: num },
      createdAt: now,
    }
    pushAudit(ev)
    return HttpResponse.json(r)
  }),

  http.get('/requests/:id', ({ params }) => {
    const id = params.id as string
    const r = getRequest(id)
    if (!r) return err(404, 'NOT_FOUND', 'Заявка не найдена')
    if (!canAccessRequest(r, role())) return err(403, 'FORBIDDEN', 'Нет доступа')
    return HttpResponse.json(r)
  }),

  http.post('/requests/:id/cancel', ({ params }) => {
    const id = params.id as string
    const r = getRequest(id)
    if (!r) return err(404, 'NOT_FOUND', 'Заявка не найдена')
    const uid = getSessionResponse().user.id
    if (r.initiator.id !== uid) return err(403, 'FORBIDDEN', 'Только инициатор')
    if (r.status !== 'pending' && r.status !== 'clarification') {
      return err(409, 'INVALID_STATUS', 'Отмена недоступна для текущего статуса')
    }
    const next = touch({ ...r, status: 'cancelled' as RequestStatus })
    saveRequest(next)
    pushAudit({
      id: crypto.randomUUID(),
      requestId: id,
      type: 'cancelled',
      actorId: uid,
      actorName: getSessionResponse().user.displayName,
      payload: {},
      createdAt: new Date().toISOString(),
    })
    return HttpResponse.json(next)
  }),

  http.post('/requests/:id/clarification/answer', async ({ params, request }) => {
    const id = params.id as string
    const r = getRequest(id)
    if (!r) return err(404, 'NOT_FOUND', 'Заявка не найдена')
    const uid = getSessionResponse().user.id
    if (r.initiator.id !== uid) return err(403, 'FORBIDDEN', 'Только инициатор')
    if (r.status !== 'clarification') {
      return err(409, 'INVALID_STATUS', 'Ответ возможен только при статусе «уточнение»')
    }
    let body: { answer: string }
    try {
      body = (await request.json()) as { answer: string }
    } catch {
      return err(400, 'BAD_JSON', 'Некорректное тело запроса')
    }
    if (!body.answer?.trim()) return err(400, 'VALIDATION', 'Введите ответ', 'answer')
    const clar = r.clarification
      ? { ...r.clarification, answer: body.answer.trim() }
      : { question: '', answer: body.answer.trim() }
    const next = touch({
      ...r,
      status: 'pending',
      clarification: clar,
    })
    saveRequest(next)
    pushAudit({
      id: crypto.randomUUID(),
      requestId: id,
      type: 'clarification_answered',
      actorId: uid,
      actorName: getSessionResponse().user.displayName,
      payload: {},
      createdAt: new Date().toISOString(),
    })
    return HttpResponse.json(next)
  }),

  http.get('/requests/:id/audit', ({ params }) => {
    const id = params.id as string
    const r = getRequest(id)
    if (!r) return err(404, 'NOT_FOUND', 'Заявка не найдена')
    if (!canAccessRequest(r, role())) return err(403, 'FORBIDDEN', 'Нет доступа')
    return HttpResponse.json(listAudit(id))
  }),

  http.get('/admin/requests', ({ request }) => {
    if (role() !== 'admin' && role() !== 'tech_admin') {
      return err(403, 'FORBIDDEN', 'Нужна роль администратора')
    }
    const url = new URL(request.url)
    const st = url.searchParams.get('status') as RequestStatus | null
    if (!st) return err(400, 'VALIDATION', 'Нужен query status', 'status')
    const list = allRequests().filter((r) => r.status === st)
    return HttpResponse.json(list)
  }),

  http.post('/admin/requests/:id/approve', async ({ params, request }) => {
    if (role() !== 'admin' && role() !== 'tech_admin') return err(403, 'FORBIDDEN', 'Нужна роль администратора')
    const id = params.id as string
    const r = getRequest(id)
    if (!r) return err(404, 'NOT_FOUND', 'Заявка не найдена')
    if (r.status !== 'pending') return err(409, 'INVALID_STATUS', 'Доступно только в статусе «на рассмотрении»')
    let body: { comment?: string } = {}
    try {
      const t = await request.text()
      if (t) body = JSON.parse(t) as { comment?: string }
    } catch {
      return err(400, 'BAD_JSON', 'Некорректное тело запроса')
    }
    const adm = getSessionResponse().user
    const next = touch({
      ...r,
      status: 'approved',
      decision: { byId: adm.id, byName: adm.displayName, comment: body.comment },
    })
    saveRequest(next)
    pushAudit({
      id: crypto.randomUUID(),
      requestId: id,
      type: 'approved',
      actorId: adm.id,
      actorName: adm.displayName,
      payload: {},
      createdAt: new Date().toISOString(),
    })
    return HttpResponse.json(next)
  }),

  http.post('/admin/requests/:id/reject', async ({ params, request }) => {
    if (role() !== 'admin' && role() !== 'tech_admin') return err(403, 'FORBIDDEN', 'Нужна роль администратора')
    const id = params.id as string
    const r = getRequest(id)
    if (!r) return err(404, 'NOT_FOUND', 'Заявка не найдена')
    if (r.status !== 'pending') return err(409, 'INVALID_STATUS', 'Доступно только в статусе «на рассмотрении»')
    let body: { reasonCode: RejectReason; comment?: string }
    try {
      body = (await request.json()) as { reasonCode: RejectReason; comment?: string }
    } catch {
      return err(400, 'BAD_JSON', 'Некорректное тело запроса')
    }
    if (!body.reasonCode) return err(400, 'VALIDATION', 'Нужна причина', 'reasonCode')
    const adm = getSessionResponse().user
    const next = touch({
      ...r,
      status: 'rejected',
      decision: {
        byId: adm.id,
        byName: adm.displayName,
        comment: body.comment,
        reason: body.reasonCode,
      },
    })
    saveRequest(next)
    pushAudit({
      id: crypto.randomUUID(),
      requestId: id,
      type: 'rejected',
      actorId: adm.id,
      actorName: adm.displayName,
      payload: { reasonCode: body.reasonCode },
      createdAt: new Date().toISOString(),
    })
    return HttpResponse.json(next)
  }),

  http.post('/admin/requests/:id/clarify', async ({ params, request }) => {
    if (role() !== 'admin' && role() !== 'tech_admin') return err(403, 'FORBIDDEN', 'Нужна роль администратора')
    const id = params.id as string
    const r = getRequest(id)
    if (!r) return err(404, 'NOT_FOUND', 'Заявка не найдена')
    if (r.status !== 'pending') return err(409, 'INVALID_STATUS', 'Доступно только в статусе «на рассмотрении»')
    let body: { question: string }
    try {
      body = (await request.json()) as { question: string }
    } catch {
      return err(400, 'BAD_JSON', 'Некорректное тело запроса')
    }
    if (!body.question?.trim()) return err(400, 'VALIDATION', 'Введите вопрос', 'question')
    const adm = getSessionResponse().user
    const next = touch({
      ...r,
      status: 'clarification',
      clarification: { question: body.question.trim(), answer: r.clarification?.answer },
    })
    saveRequest(next)
    pushAudit({
      id: crypto.randomUUID(),
      requestId: id,
      type: 'clarification_requested',
      actorId: adm.id,
      actorName: adm.displayName,
      payload: { preview: body.question.trim().slice(0, 80) },
      createdAt: new Date().toISOString(),
    })
    return HttpResponse.json(next)
  }),

  http.post('/admin/requests/:id/close', ({ params }) => {
    if (role() !== 'admin' && role() !== 'tech_admin') return err(403, 'FORBIDDEN', 'Нужна роль администратора')
    const id = params.id as string
    const r = getRequest(id)
    if (!r) return err(404, 'NOT_FOUND', 'Заявка не найдена')
    if (r.status !== 'approved' && r.status !== 'rejected') {
      return err(409, 'INVALID_STATUS', 'Закрыть можно только одобренные или отклонённые')
    }
    const adm = getSessionResponse().user
    const next = touch({ ...r, status: 'closed' })
    saveRequest(next)
    pushAudit({
      id: crypto.randomUUID(),
      requestId: id,
      type: 'closed',
      actorId: adm.id,
      actorName: adm.displayName,
      payload: {},
      createdAt: new Date().toISOString(),
    })
    return HttpResponse.json(next)
  }),
]
