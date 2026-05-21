import { Button, CellList, CellSimple, Flex, Input, Panel, Textarea, Typography } from '@maxhub/max-ui'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { useRequestDraftStore } from '../../features/request/draftStore'
import {
  createRequestSchema,
  guestFullNameSchema,
  purposeSchema,
  visitDateSchema,
  visitTimeSchema,
  zoneIdSchema,
} from '../../features/request/schemas'
import { requestKeys, useZonesQuery } from '../../features/request/queries'
import { api } from '../../shared/api/client'
import { todayIsoDate } from '../../shared/lib/dates'
import { VISIT_TIME_OPTIONS } from '../../shared/lib/visitTime'
import { AppScreen } from '../../shared/ui/AppScreen'

const STEPS = ['guest', 'date', 'time', 'zone', 'purpose', 'confirm'] as const
type Step = (typeof STEPS)[number]

const STEP_FIELD_NAMES: Record<Step, string> = {
  guest: 'ФИО гостя',
  date: 'Дата визита',
  time: 'Время визита',
  zone: 'Зона / корпус',
  purpose: 'Цель визита',
  confirm: 'Данные заявки',
}

function isStep(s: string | undefined): s is Step {
  return !!s && (STEPS as readonly string[]).includes(s)
}

function stepIndex(s: Step): number {
  return STEPS.indexOf(s) + 1
}

function nextStep(s: Step): Step | null {
  const i = STEPS.indexOf(s)
  return STEPS[i + 1] ?? null
}

function prevStep(s: Step): Step | null {
  const i = STEPS.indexOf(s)
  return i > 0 ? STEPS[i - 1]! : null
}

export function NewRequestPage() {
  const { step: stepParam } = useParams<{ step: string }>()
  const nav = useNavigate()
  const qc = useQueryClient()
  const zones = useZonesQuery()
  const draft = useRequestDraftStore((s) => s.draft)
  const patch = useRequestDraftStore((s) => s.patch)
  const reset = useRequestDraftStore((s) => s.reset)
  const [fieldError, setFieldError] = useState<string | null>(null)

  useEffect(() => {
    if (stepParam === 'date' && !draft.visitDate) {
      patch({ visitDate: todayIsoDate() })
    }
  }, [stepParam, draft.visitDate, patch])

  const createMut = useMutation({
    mutationFn: () =>
      api.createRequest({
        guestFullName: draft.guestFullName.trim(),
        visitDate: draft.visitDate,
        visitTime: draft.visitTime as 'morning' | 'day' | 'evening',
        zoneId: draft.zoneId,
        purpose: draft.purpose.trim(),
      }),
    onSuccess: async (created) => {
      reset()
      await qc.invalidateQueries({ queryKey: requestKeys.mine })
      nav(`/requests/${created.id}`, { replace: true })
    },
  })

  if (!isStep(stepParam)) {
    return <Navigate to="/requests/new/guest" replace />
  }
  const step = stepParam

  const goNext = () => {
    setFieldError(null)
    if (step === 'guest') {
      const r = guestFullNameSchema.safeParse(draft.guestFullName)
      if (!r.success) {
        setFieldError(r.error.errors[0]?.message ?? 'Ошибка')
        return
      }
    }
    if (step === 'date') {
      const r = visitDateSchema.safeParse(draft.visitDate)
      if (!r.success) {
        setFieldError(r.error.errors[0]?.message ?? 'Ошибка')
        return
      }
    }
    if (step === 'time') {
      const r = visitTimeSchema.safeParse(draft.visitTime)
      if (!r.success) {
        setFieldError('Выберите время визита')
        return
      }
    }
    if (step === 'zone') {
      const r = zoneIdSchema.safeParse(draft.zoneId)
      if (!r.success) {
        setFieldError(r.error.errors[0]?.message ?? 'Ошибка')
        return
      }
    }
    if (step === 'purpose') {
      const r = purposeSchema.safeParse(draft.purpose)
      if (!r.success) {
        setFieldError(r.error.errors[0]?.message ?? 'Ошибка')
        return
      }
    }
    const n = nextStep(step)
    if (n) nav(`/requests/new/${n}`)
  }

  const goPrev = () => {
    setFieldError(null)
    const p = prevStep(step)
    if (p) nav(`/requests/new/${p}`)
    else nav('/')
  }

  const cancelWizard = () => {
    reset()
    nav('/')
  }

  const submit = () => {
    setFieldError(null)
    const parsed = createRequestSchema.safeParse({
      guestFullName: draft.guestFullName,
      visitDate: draft.visitDate,
      visitTime: draft.visitTime,
      zoneId: draft.zoneId,
      purpose: draft.purpose,
    })
    if (!parsed.success) {
      setFieldError(parsed.error.errors[0]?.message ?? 'Проверьте поля')
      return
    }
    createMut.mutate()
  }

  const title = `Новая заявка (${stepIndex(step)}/${STEPS.length})`

  return (
    <AppScreen
      title={title}
      footer={
        <Flex direction="column" gap={8}>
          {step === 'confirm' ? (
            <>
              <Button mode="primary" loading={createMut.isPending} onClick={submit}>
                Подтвердить
              </Button>
              <Button mode="secondary" onClick={cancelWizard}>
                Отменить (удалить черновик)
              </Button>
            </>
          ) : (
            <>
              <Button mode="primary" onClick={goNext}>
                Далее
              </Button>
              <Button mode="tertiary" onClick={goPrev}>
                Назад
              </Button>
              <Button mode="tertiary" appearance="negative" onClick={cancelWizard}>
                Отменить мастер
              </Button>
            </>
          )}
        </Flex>
      }
    >
      {fieldError && (
        <Panel mode="secondary" style={{ border: '1px solid #ff4d4f', background: 'rgba(255, 77, 79, 0.05)', borderRadius: 12 }}>
          <Flex direction="column" gap={8} style={{ padding: 12 }} align="center">
            <Typography.Body style={{ color: '#ff4d4f', fontWeight: 'bold' }}>
              Ошибка в шаге «{STEP_FIELD_NAMES[step]}»
            </Typography.Body>
            <Typography.Body style={{ color: '#ff4d4f', textAlign: 'center' }}>
              {fieldError}
            </Typography.Body>
            <Button size="small" mode="secondary" onClick={() => setFieldError(null)}>
              Исправить
            </Button>
          </Flex>
        </Panel>
      )}

      {step === 'guest' ? (
        <Flex direction="column" gap={8}>
          <Typography.Body>ФИО гостя</Typography.Body>
          <Input
            value={draft.guestFullName}
            onChange={(e) => {
              setFieldError(null)
              patch({ guestFullName: e.target.value })
            }}
            placeholder="Иванов Иван Иванович"
          />
        </Flex>
      ) : null}

      {step === 'date' ? (
        <Flex direction="column" gap={8}>
          <Typography.Body>Дата визита</Typography.Body>
          <Input
            type="date"
            value={draft.visitDate}
            onChange={(e) => {
              setFieldError(null)
              patch({ visitDate: e.target.value })
            }}
          />
        </Flex>
      ) : null}

      {step === 'time' ? (
        <Flex direction="column" gap={8}>
          <Typography.Body>Время</Typography.Body>
          <CellList mode="island">
            {VISIT_TIME_OPTIONS.map((o) => (
              <CellSimple
                as="button"
                key={o.value}
                onClick={() => {
                  setFieldError(null)
                  patch({ visitTime: o.value })
                }}
                title={o.label}
                after={draft.visitTime === o.value ? <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--max-ui-accent, #aa3bff)' }} /> : null}
              />
            ))}
          </CellList>
        </Flex>
      ) : null}

      {step === 'zone' ? (
        <Flex direction="column" gap={8}>
          <Typography.Body>Зона / корпус</Typography.Body>
          {zones.isLoading ? <Typography.Body>Загрузка зон…</Typography.Body> : null}
          {zones.data ? (
            <CellList mode="island">
              {zones.data.map((z) => (
                <CellSimple
                  as="button"
                  key={z.id}
                  onClick={() => {
                    setFieldError(null)
                    patch({ zoneId: z.id })
                  }}
                  title={z.title}
                  after={draft.zoneId === z.id ? <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--max-ui-accent, #aa3bff)' }} /> : null}
                />
              ))}
            </CellList>
          ) : null}
        </Flex>
      ) : null}

      {step === 'purpose' ? (
        <Flex direction="column" gap={8}>
          <Typography.Body>Цель визита</Typography.Body>
          <Textarea
            value={draft.purpose}
            onChange={(e) => {
              setFieldError(null)
              patch({ purpose: e.target.value })
            }}
            placeholder="Кратко опишите цель"
          />
        </Flex>
      ) : null}

      {step === 'confirm' ? (
        <Flex direction="column" gap={8}>
          <Typography.Title>Сводка</Typography.Title>
          <Panel mode="primary">
            <Flex direction="column" gap={0}>
              <CellSimple title="Гость" subtitle={draft.guestFullName} />
              <CellSimple title="Дата" subtitle={draft.visitDate} />
              <CellSimple
                title="Время"
                subtitle={VISIT_TIME_OPTIONS.find((x) => x.value === draft.visitTime)?.label ?? draft.visitTime}
              />
              <CellSimple
                title="Зона"
                subtitle={zones.data?.find((z) => z.id === draft.zoneId)?.title ?? draft.zoneId}
              />
              <CellSimple title="Цель" subtitle={draft.purpose} />
            </Flex>
          </Panel>
        </Flex>
      ) : null}
    </AppScreen>
  )
}
