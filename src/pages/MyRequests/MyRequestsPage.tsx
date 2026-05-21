import { CellAction, CellList, Typography } from '@maxhub/max-ui'
import { useNavigate } from 'react-router-dom'
import { useMyRequestsQuery } from '../../features/request/queries'
import { formatRuDate } from '../../shared/lib/dates'
import { requestStatusLabel } from '../../shared/lib/statusLabels'
import { AppScreen } from '../../shared/ui/AppScreen'

export function MyRequestsPage() {
  const nav = useNavigate()
  const q = useMyRequestsQuery()

  return (
    <AppScreen title="Мои заявки">
      {q.isLoading ? <Typography.Body>Загрузка…</Typography.Body> : null}
      {q.isError ? <Typography.Body>Не удалось загрузить список.</Typography.Body> : null}
      {q.data?.length === 0 ? (
        <Typography.Body variant="small">Пока нет заявок. Создайте новую с главной.</Typography.Body>
      ) : null}
      {q.data && q.data.length > 0 ? (
        <CellList mode="island">
          {q.data.map((r) => (
            <CellAction
              key={r.id}
              onClick={() => nav(`/requests/${r.id}`)}
              showChevron
            >
              {r.number} · {formatRuDate(r.visitDate)} · {requestStatusLabel(r.status)}
            </CellAction>
          ))}
        </CellList>
      ) : null}
    </AppScreen>
  )
}
