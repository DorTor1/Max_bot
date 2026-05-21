import { Button, CellSimple, Flex, Input, Panel, Textarea, Typography } from '@maxhub/max-ui'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { AuditFeed } from '../../../features/audit/AuditFeed'
import { requestKeys, useAuditQuery, useRequestQuery } from '../../../features/request/queries'
import type { RejectReason } from '../../../shared/api/client'
import { api } from '../../../shared/api/client'
import { formatRuDate } from '../../../shared/lib/dates'
import { requestStatusLabel } from '../../../shared/lib/statusLabels'
import { VISIT_TIME_OPTIONS } from '../../../shared/lib/visitTime'
import { AppScreen } from '../../../shared/ui/AppScreen'

const REJECT_OPTIONS: { value: RejectReason; label: string }[] = [
  { value: 'INVALID_DATA', label: 'Некорректные данные' },
  { value: 'SECURITY_POLICY', label: 'Политика безопасности' },
  { value: 'DUPLICATE', label: 'Дубликат заявки' },
  { value: 'OTHER', label: 'Другое' },
]

export function AdminRequestCardPage() {
  const { id } = useParams<{ id: string }>()
  const nav = useNavigate()
  const qc = useQueryClient()
  const rq = useRequestQuery(id)
  const aq = useAuditQuery(id)

  const [commentApprove, setCommentApprove] = useState('')
  const [reason, setReason] = useState<RejectReason>('INVALID_DATA')
  const [commentReject, setCommentReject] = useState('')
  const [question, setQuestion] = useState('')

  const inv = async () => {
    await qc.invalidateQueries({ queryKey: requestKeys.one(id!) })
    await qc.invalidateQueries({ queryKey: requestKeys.adminQueue })
    await qc.invalidateQueries({ queryKey: requestKeys.audit(id!) })
  }

  const approve = useMutation({
    mutationFn: () => api.adminApprove(id!, { comment: commentApprove || undefined }),
    onSuccess: inv,
  })
  const reject = useMutation({
    mutationFn: () =>
      api.adminReject(id!, { reasonCode: reason, comment: commentReject || undefined }),
    onSuccess: inv,
  })
  const clarify = useMutation({
    mutationFn: () => api.adminClarify(id!, { question }),
    onSuccess: async () => {
      setQuestion('')
      await inv()
    },
  })
  const close = useMutation({
    mutationFn: () => api.adminClose(id!),
    onSuccess: inv,
  })

  if (!id) return null

  if (rq.isLoading || !rq.data) {
    return (
      <AppScreen title="Заявка">
        <Typography.Body>Загрузка…</Typography.Body>
      </AppScreen>
    )
  }

  const r = rq.data
  const pending = r.status === 'pending'
  const canClose = r.status === 'approved' || r.status === 'rejected'

  return (
    <AppScreen
      title={r.number}
      footer={
        <Button mode="secondary" onClick={() => nav('/admin/queue')}>
          К очереди
        </Button>
      }
    >
      <Typography.Body variant="small">{requestStatusLabel(r.status)}</Typography.Body>
      <Panel mode="primary">
        <Flex direction="column" gap={0}>
          <CellSimple title="Инициатор" subtitle={r.initiator.displayName} />
          <CellSimple title="Гость" subtitle={r.guestFullName} />
          <CellSimple title="Дата" subtitle={formatRuDate(r.visitDate)} />
          <CellSimple
            title="Время"
            subtitle={VISIT_TIME_OPTIONS.find((x) => x.value === r.visitTime)?.label ?? r.visitTime}
          />
          <CellSimple title="Зона" subtitle={r.zone} />
          <CellSimple title="Цель" subtitle={r.purpose} />
        </Flex>
      </Panel>

      {pending ? (
        <Panel mode="secondary">
          <Flex direction="column" gap={12} style={{ padding: 12 }}>
            <Typography.Title>Действия</Typography.Title>
            <Input
              placeholder="Комментарий (при одобрении)"
              value={commentApprove}
              onChange={(e) => setCommentApprove(e.target.value)}
            />
            <Button mode="primary" loading={approve.isPending} onClick={() => approve.mutate()}>
              Подтвердить
            </Button>
            <Typography.Title>Отклонить</Typography.Title>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value as RejectReason)}
              style={{ padding: 8, borderRadius: 8 }}
            >
              {REJECT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            <Input
              placeholder="Комментарий (необязательно)"
              value={commentReject}
              onChange={(e) => setCommentReject(e.target.value)}
            />
            <Button
              mode="primary"
              appearance="negative"
              loading={reject.isPending}
              onClick={() => reject.mutate()}
            >
              Отклонить
            </Button>
            <Typography.Title>Запросить уточнение</Typography.Title>
            <Textarea value={question} onChange={(e) => setQuestion(e.target.value)} />
            <Button
              mode="secondary"
              loading={clarify.isPending}
              disabled={question.trim().length < 3}
              onClick={() => clarify.mutate()}
            >
              Отправить вопрос
            </Button>
          </Flex>
        </Panel>
      ) : null}

      {canClose ? (
        <Flex direction="column" gap={8}>
          <Button mode="primary" loading={close.isPending} onClick={() => close.mutate()}>
            Закрыть заявку
          </Button>
        </Flex>
      ) : null}

      <AuditFeed events={aq.data} />
    </AppScreen>
  )
}
