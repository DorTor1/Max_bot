import { CellList, CellSimple, Counter, Typography } from '@maxhub/max-ui'
import { useNavigate } from 'react-router-dom'
import { useAdminQueueQuery } from '../../../features/request/queries'
import { formatRuDate } from '../../../shared/lib/dates'
import { AppScreen } from '../../../shared/ui/AppScreen'

export function AdminQueuePage() {
  const nav = useNavigate()
  const q = useAdminQueueQuery()

  return (
    <AppScreen title="Очередь ИБ">
      <Typography.Body variant="small" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        В очереди: <Counter value={q.data?.length ?? 0} />
      </Typography.Body>
      {q.isLoading ? <Typography.Body>Загрузка…</Typography.Body> : null}
      {q.isError ? <Typography.Body>Ошибка загрузки очереди.</Typography.Body> : null}
      {q.data?.length === 0 ? (
        <Typography.Body variant="small">Нет заявок в статусе «на рассмотрении».</Typography.Body>
      ) : null}
      {q.data && q.data.length > 0 ? (
        <CellList mode="island">
          {q.data.map((r) => (
            <CellSimple
              as="button"
              key={r.id}
              onClick={() => nav(`/admin/requests/${r.id}`)}
              showChevron
              title={r.guestFullName}
              subtitle={`${r.number} · ${formatRuDate(r.visitDate)}`}
              overline={`Инициатор: ${r.initiator.displayName}`}
              after={
                <Typography.Label variant="medium-strong">
                  {r.zone}
                </Typography.Label>
              }
            />
          ))}
        </CellList>
      ) : null}
    </AppScreen>
  )
}
