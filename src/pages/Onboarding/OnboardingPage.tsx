import { Button, Flex, Panel, Typography } from '@maxhub/max-ui'
import { useQueryClient } from '@tanstack/react-query'
import { Navigate, useNavigate } from 'react-router-dom'
import { useConsentMutation, useSessionQuery, sessionKeys } from '../../features/auth/session'
import { AppScreen } from '../../shared/ui/AppScreen'

export function OnboardingPage() {
  const nav = useNavigate()
  const qc = useQueryClient()
  const { data, isPending, isError, refetch } = useSessionQuery()
  const consent = useConsentMutation()

  if (isPending) {
    return (
      <AppScreen title="Загрузка…">
        <Typography.Body>Получаем настройки профиля…</Typography.Body>
      </AppScreen>
    )
  }

  if (isError || !data) {
    return (
      <AppScreen title="Ошибка" footer={<Button onClick={() => refetch()}>Повторить</Button>}>
        <Typography.Body>Не удалось загрузить сессию.</Typography.Body>
      </AppScreen>
    )
  }

  if (!data.consent.required) {
    return <Navigate to="/" replace />
  }

  return (
    <AppScreen
      title="Согласие"
      footer={
        <Button
          stretched
          mode="primary"
          loading={consent.isPending}
          onClick={async () => {
            await consent.mutateAsync(data.consent.version)
            await qc.refetchQueries({ queryKey: sessionKeys.session })
            nav('/', { replace: true })
          }}
        >
          Принять и продолжить
        </Button>
      }
    >
      <Panel mode="primary">
        <Flex direction="column" gap={12} style={{ padding: 16 }}>
          <Typography.Display>Политика и дисклеймер</Typography.Display>
          <Typography.Body>
            Сервис «Электронное бюро пропусков» обрабатывает персональные данные в рамках оформления
            разового гостевого пропуска. Продолжая, вы подтверждаете ознакомление с правилами посещения
            и согласие на обработку данных (версия {data.consent.version}).
          </Typography.Body>
          <Typography.Body variant="small">
            Роль и права определяются только на сервере после обмена с MAX SDK.
          </Typography.Body>
        </Flex>
      </Panel>
      {consent.isError ? (
        <Typography.Body variant="small">Не удалось сохранить согласие. Попробуйте снова.</Typography.Body>
      ) : null}
    </AppScreen>
  )
}
