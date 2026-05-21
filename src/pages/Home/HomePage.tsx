import { Button, CellAction, CellList, Counter, Flex, Panel, Typography } from '@maxhub/max-ui'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useSessionQuery, sessionKeys } from '../../features/auth/session'
import { useAdminQueueQuery } from '../../features/request/queries'
import { AppScreen } from '../../shared/ui/AppScreen'

export function HomePage() {
  const nav = useNavigate()
  const qc = useQueryClient()
  const { data } = useSessionQuery()
  const role = data?.role
  const isAdmin = role === 'admin' || role === 'tech_admin'
  const queue = useAdminQueueQuery({ enabled: isAdmin })

  const toggleRole = async () => {
    const nextRole = role === 'initiator' ? 'admin' : 'initiator'
    localStorage.setItem('MOCK_ROLE', nextRole)
    await qc.invalidateQueries({ queryKey: sessionKeys.session })
  }

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
        <Panel mode="secondary" style={{ padding: 12, borderRadius: 12 }}>
          <Flex direction="column" gap={8} align="center">
            <Typography.Label variant="medium">Панель отладки</Typography.Label>
            <Button size="small" mode="secondary" onClick={toggleRole}>
              Сменить роль на {role === 'initiator' ? 'Инженер ИБ' : 'Инициатор'}
            </Button>
          </Flex>
        </Panel>
        <Button mode="tertiary" onClick={() => nav('/onboarding')}>
          К экрану согласия
        </Button>
      </Flex>
    </AppScreen>
  )
}
