import { Button, CellSimple, Flex, Panel, Textarea, Typography } from '@maxhub/max-ui'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate, useParams, Navigate } from 'react-router-dom'
import { AuditFeed } from '../../features/audit/AuditFeed'
import { requestKeys, useAuditQuery, useRequestQuery } from '../../features/request/queries'
import { api } from '../../shared/api/client'
import { formatRuDate } from '../../shared/lib/dates'
import { requestStatusLabel } from '../../shared/lib/statusLabels'
import { VISIT_TIME_OPTIONS } from '../../shared/lib/visitTime'
import { AppScreen } from '../../shared/ui/AppScreen'

export function RequestDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const nav = useNavigate()
  const qc = useQueryClient()
  const rq = useRequestQuery(id)
  const aq = useAuditQuery(id)
  const [answer, setAnswer] = useState('')

  const invalidate = async () => {
    await qc.invalidateQueries({ queryKey: requestKeys.one(id!) })
    await qc.invalidateQueries({ queryKey: requestKeys.mine })
    await qc.invalidateQueries({ queryKey: requestKeys.audit(id!) })
  }

  const cancelMut = useMutation({
    mutationFn: () => api.cancelRequest(id!),
    onSuccess: invalidate,
  })

  const answerMut = useMutation({
    mutationFn: () => api.answerClarification(id!, { answer }),
    onSuccess: async () => {
      setAnswer('')
      await invalidate()
    },
  })

  if (id === 'new') {
    return <Navigate to="/requests/new/guest" replace />
  }

  if (!id) return null

  if (rq.isLoading || !rq.data) {
    return (
      <AppScreen title="Заявка">
        <Typography.Body>Загрузка…</Typography.Body>
      </AppScreen>
    )
  }

  const r = rq.data
  const canCancel = r.status === 'pending' || r.status === 'clarification'

  return (
    <AppScreen
      title={r.number}
      footer={
        <Flex direction="column" gap={8}>
          <Button mode="secondary" onClick={() => nav(-1)}>
            Назад
          </Button>
          {canCancel ? (
            <Button
              mode="primary"
              appearance="negative"
              loading={cancelMut.isPending}
              onClick={() => cancelMut.mutate()}
            >
              Отменить заявку
            </Button>
          ) : null}
        </Flex>
      }
    >
      <Typography.Body variant="small">{requestStatusLabel(r.status)}</Typography.Body>
      <Panel mode="primary">
        <Flex direction="column" gap={0}>
          <CellSimple title="Гость" subtitle={r.guestFullName} />
          <CellSimple title="Дата визита" subtitle={formatRuDate(r.visitDate)} />
          <CellSimple
            title="Время"
            subtitle={VISIT_TIME_OPTIONS.find((x) => x.value === r.visitTime)?.label ?? r.visitTime}
          />
          <CellSimple title="Зона" subtitle={r.zone} />
          <CellSimple title="Цель" subtitle={r.purpose} />
        </Flex>
      </Panel>
      {r.clarification?.question ? (
        <Panel mode="secondary">
          <Flex direction="column" gap={8} style={{ padding: 12 }}>
            <Typography.Title>Вопрос от ИБ</Typography.Title>
            <Typography.Body>{r.clarification.question}</Typography.Body>
            {r.clarification.answer ? (
              <Typography.Body variant="small">Ваш ответ: {r.clarification.answer}</Typography.Body>
            ) : null}
          </Flex>
        </Panel>
      ) : null}
      {r.status === 'clarification' && !r.clarification?.answer ? (
        <Flex direction="column" gap={8}>
          <Typography.Title>Ответ на уточнение</Typography.Title>
          <Textarea value={answer} onChange={(e) => setAnswer(e.target.value)} placeholder="Ваш ответ" />
          <Button
            mode="primary"
            loading={answerMut.isPending}
            onClick={() => answerMut.mutate()}
            disabled={!answer.trim()}
          >
            Отправить ответ
          </Button>
        </Flex>
      ) : null}
      {r.decision ? (
        <Panel mode="primary">
          <Flex direction="column" gap={8} style={{ padding: 12 }}>
            <Typography.Title>Решение</Typography.Title>
            <Typography.Body>
              {r.decision.byName}
              {r.decision.reason ? ` · ${r.decision.reason}` : ''}
            </Typography.Body>
            {r.decision.comment ? <Typography.Body variant="small">{r.decision.comment}</Typography.Body> : null}
          </Flex>
        </Panel>
      ) : null}
      <AuditFeed events={aq.data} />
    </AppScreen>
  )
}
