import { Button, CellAction, CellList, Counter, Flex, Typography } from '@maxhub/max-ui'
import { useNavigate } from 'react-router-dom'
import { useSessionQuery } from '../../features/auth/session'
import { useAdminQueueQuery } from '../../features/request/queries'
import { AppScreen } from '../../shared/ui/AppScreen'

export function HomePage() {
  const nav = useNavigate()
  const { data } = useSessionQuery()
  const role = data?.role
  const isAdmin = role === 'admin' || role === 'tech_admin'
  const queue = useAdminQueueQuery({ enabled: isAdmin })

  return (
    <AppScreen title="Бюро пропусков">
      <Typography.Body variant="small">
        {data?.user.displayName} ·{' '}
        {role === 'admin' || role === 'tech_admin' ? 'Инженер ИБ' : 'Инициатор'}
      </Typography.Body>
      <CellList mode="island" header={<Typography.Title>Действия</Typography.Title>}>
        {role === 'initiator' ? (
          <>
            <CellAction onClick={() => nav('/requests/new/guest')} showChevron>
              Создать пропуск
            </CellAction>
            <CellAction onClick={() => nav('/requests')} showChevron>
              Мои заявки
            </CellAction>
          </>
        ) : null}
        {isAdmin ? (
          <CellAction
            onClick={() => nav('/admin/queue')}
            showChevron
            before={<Counter value={queue.data?.length ?? 0} muted />}
          >
            Очередь ИБ
          </CellAction>
        ) : null}
      </CellList>
      <Flex direction="column" gap={8}>
        <Typography.Label variant="medium">
          Подсказка: роль в моках задаётся в .env (VITE_MOCK_ROLE).
        </Typography.Label>
        <Button mode="tertiary" onClick={() => nav('/onboarding')}>
          К экрану согласия
        </Button>
      </Flex>
    </AppScreen>
  )
}
