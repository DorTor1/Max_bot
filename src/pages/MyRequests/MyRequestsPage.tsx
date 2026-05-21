import { CellList, CellSimple, Dot, Flex, Typography } from '@maxhub/max-ui'
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
            <CellSimple
              as="button"
              key={r.id}
              onClick={() => nav(`/requests/${r.id}`)}
              showChevron
              title={r.number}
              subtitle={`${r.guestFullName} · ${formatRuDate(r.visitDate)}`}
              after={
                <Flex align="center" gap={8}>
                  <Typography.Label variant="medium-strong">
                    {requestStatusLabel(r.status)}
                  </Typography.Label>
                  <Dot
                    appearance={
                      r.status === 'approved'
                        ? 'themed'
                        : r.status === 'rejected'
                          ? 'accent-red'
                          : r.status === 'pending' || r.status === 'clarification'
                            ? 'themed'
                            : 'neutral-fade'
                    }
                  />
                </Flex>
              }
            />
          ))}
        </CellList>
      ) : null}
    </AppScreen>
  )
}
