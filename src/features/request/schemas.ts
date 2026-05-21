import { z } from 'zod'
import { todayIsoDate } from '../../shared/lib/dates'

export const visitTimeSchema = z.enum(['morning', 'day', 'evening'])

export const guestFullNameSchema = z
  .string()
  .trim()
  .min(2, 'Минимум 2 символа')
  .max(120, 'Максимум 120 символов')
  .refine((v) => /[^\d\s]/.test(v), 'ФИО не должно состоять только из цифр и пробелов')

export const purposeSchema = z
  .string()
  .trim()
  .min(3, 'Минимум 3 символа')
  .max(500, 'Максимум 500 символов')

export const visitDateSchema = z.string().refine((iso) => {
  const t = todayIsoDate()
  return iso >= t
}, 'Дата не может быть в прошлом')

export const zoneIdSchema = z.string().min(1, 'Выберите зону')

export const createRequestSchema = z.object({
  guestFullName: guestFullNameSchema,
  visitDate: visitDateSchema,
  visitTime: visitTimeSchema,
  zoneId: zoneIdSchema,
  purpose: purposeSchema,
})

export type CreateRequestForm = z.infer<typeof createRequestSchema>
