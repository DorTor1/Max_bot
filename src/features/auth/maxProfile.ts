const w = window as Window & {
  max?: { getUser?: () => Promise<{ id: string; displayName?: string; name?: string }> }
}

export type MaxUser = { id: string; displayName: string }

/**
 * Профиль из MAX SDK в проде; в разработке — переменные окружения.
 */
export async function readMaxUser(): Promise<MaxUser> {
  try {
    const g = w.max?.getUser
    if (g) {
      const u = await g()
      const displayName = u.displayName ?? u.name ?? 'Пользователь'
      return { id: u.id, displayName }
    }
  } catch {
    /* SDK недоступен */
  }
  return {
    id: import.meta.env.VITE_MOCK_USER_ID || 'user-demo-1',
    displayName: import.meta.env.VITE_MOCK_USER_NAME || 'Иван Инициатор',
  }
}
