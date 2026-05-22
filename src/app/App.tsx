import { Button, Flex, Spinner, Typography } from '@maxhub/max-ui'
import { HashRouter, Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { RequireRole } from '../features/auth/RequireRole'
import { useSessionQuery } from '../features/auth/session'
import { AdminQueuePage } from '../pages/Admin/Queue/AdminQueuePage'
import { AdminRequestCardPage } from '../pages/Admin/RequestCard/AdminRequestCardPage'
import { HomePage } from '../pages/Home/HomePage'
import { MyRequestsPage } from '../pages/MyRequests/MyRequestsPage'
import { NewRequestPage } from '../pages/NewRequest/NewRequestPage'
import { OnboardingPage } from '../pages/Onboarding/OnboardingPage'
import { RequestDetailsPage } from '../pages/RequestDetails/RequestDetailsPage'

function AppLayout() {
  const { data, isPending, isError, refetch } = useSessionQuery()
  const loc = useLocation()

  if (isPending) {
    return (
      <Flex
        direction="column"
        align="center"
        justify="center"
        gap={12}
        className="h-screen"
      >
        <Spinner />
        <Typography.Body>Загрузка сессии…</Typography.Body>
      </Flex>
    )
  }

  if (isError || !data) {
    return (
      <Flex
        direction="column"
        align="center"
        justify="center"
        gap={12}
        className="h-screen p-6"
      >
        <Typography.Title>Не удалось получить сессию</Typography.Title>
        <Button mode="primary" onClick={() => refetch()}>
          Повторить
        </Button>
      </Flex>
    )
  }

  if (data.consent.required && loc.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />
  }

  if (!data.consent.required && loc.pathname === '/onboarding') {
    return <Navigate to="/" replace />
  }

  return (
    <div className="h-full min-h-screen">
      <Outlet />
    </div>
  )
}

function AdminOutlet() {
  return (
    <RequireRole role={['admin', 'tech_admin']}>
      <Outlet />
    </RequireRole>
  )
}

export function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="/" element={<HomePage />} />
          <Route path="/requests" element={<MyRequestsPage />} />
          <Route path="/requests/new" element={<Navigate to="/requests/new/guest" replace />} />
          <Route path="/requests/new/:step" element={<NewRequestPage />} />
          <Route path="/requests/:id" element={<RequestDetailsPage />} />
          <Route element={<AdminOutlet />}>
            <Route path="/admin/queue" element={<AdminQueuePage />} />
            <Route path="/admin/requests/:id" element={<AdminRequestCardPage />} />
          </Route>
        </Route>
      </Routes>
    </HashRouter>
  )
}
