import { Flex, Panel, Typography } from '@maxhub/max-ui'
import type { AuditEvent } from '../../shared/api/client'

const typeLabels: Record<AuditEvent['type'], string> = {
  created: 'Создано',
  submitted: 'Подано на рассмотрение',
  approved: 'Одобрено',
  rejected: 'Отклонено',
  clarification_requested: 'Запрошено уточнение',
  clarification_answered: 'Получен ответ',
  cancelled: 'Отменено инициатором',
  closed: 'Закрыто',
}

function formatTs(iso: string): string {
  try {
    return new Date(iso).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

export function AuditFeed({ events }: { events: AuditEvent[] | undefined }) {
  if (!events?.length) {
    return (
      <Typography.Body variant="small">Пока нет событий в журнале.</Typography.Body>
    )
  }
  return (
    <Flex direction="column" gap={8}>
      <Typography.Title>История</Typography.Title>
      {events.map((e) => (
        <Panel key={e.id} mode="primary">
          <Flex direction="column" gap={4} style={{ padding: 12 }}>
            <Typography.Label variant="medium">{formatTs(e.createdAt)}</Typography.Label>
            <Typography.Body>
              <strong>{e.actorName}</strong> — {typeLabels[e.type]}
            </Typography.Body>
            {e.payload && typeof e.payload === 'object' && 'number' in e.payload ? (
              <Typography.Body variant="small">№ {(e.payload as { number: string }).number}</Typography.Body>
            ) : null}
            {e.payload && typeof e.payload === 'object' && 'preview' in e.payload ? (
              <Typography.Body variant="small">
                {(e.payload as { preview: string }).preview}
              </Typography.Body>
            ) : null}
            {e.payload && typeof e.payload === 'object' && 'reasonCode' in e.payload ? (
              <Typography.Body variant="small">
                Причина: {(e.payload as { reasonCode: string }).reasonCode}
              </Typography.Body>
            ) : null}
          </Flex>
        </Panel>
      ))}
    </Flex>
  )
}
