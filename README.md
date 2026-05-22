# Электронное бюро пропусков (MAX mini-app)

SPA на **Vite + React 18 + TypeScript**, UI — [`@maxhub/max-ui`](https://dev.max.ru/ui), маршрутизация — **React Router** (hash), данные — **TanStack Query**, формы — **Zod**, глобальный черновик мастера — **Zustand**. Контракт API для бэкенда: **`openapi.yaml`** (OpenAPI 3.0.3).

## Быстрый старт

```bash
cp .env.example .env
npm install
npm run dev
```

По умолчанию в `.env.example` включён режим **`VITE_API_MODE=mock`**: поднимается **MSW** и отвечает на все ручки из `openapi.yaml` без реального сервера.

Для работы с бэкендом задайте `VITE_API_MODE=real` и `VITE_API_BASE_URL` (например `http://localhost:8080`), убедитесь, что API соответствует `openapi.yaml`.

## Скрипты

| Команда | Назначение |
|--------|------------|
| `npm run dev` | Разработка |
| `npm run build` | Сборка |
| `npm run lint` | ESLint |
| `npm run generate:api` | Генерация `src/shared/api/schema.d.ts` из `openapi.yaml` (`openapi-typescript`) |

## Допущения (зафиксировано в моках)

- Номер заявки: **`GP-YYYY-NNNNNN`** (см. мок `allocateNumber` / ответ `POST /requests`).
- Кнопка «Отменить» в мастере создания: **сбрасывает черновик** в Zustand и ведёт на главную.
- Причины отклонения (`RejectReason`): `INVALID_DATA`, `SECURITY_POLICY`, `DUPLICATE`, `OTHER` — при необходимости расширьте enum в `openapi.yaml` и перегенерируйте типы.
- Справочник зон: **`GET /zones`**, начальный набор в `src/mocks/fixtures/zones.json`.
- Профиль пользователя: в проде — из MAX SDK (`window.max?.getUser` в заглушке); в dev — `VITE_MOCK_USER_ID` / `VITE_MOCK_USER_NAME`. Роль приходит только с **`POST /auth/session`**.

## Структура `src/`

- `app/` — `main.tsx`, `App.tsx`, провайдеры (MaxUI, QueryClient, HashRouter).
- `pages/` — экраны по маршрутам из ТЗ.
- `features/` — сессия, заявки, аудит.
- `shared/api/` — `client.ts`, сгенерированный `schema.d.ts`.
- `mocks/` — MSW (`handlers.ts`, `state.ts`, `fixtures/`).

## Маршруты

| Путь | Экран |
|------|--------|
| `/onboarding` | Дисклеймер и согласие |
| `/` | Главное меню (зависит от роли) |
| `/requests/new/...` | Мастер создания заявки (шаги) |
| `/requests` | Мои заявки |
| `/requests/:id` | Карточка инициатора + аудит |
| `/admin/queue` | Очередь ИБ (только `admin` / `tech_admin`) |
| `/admin/requests/:id` | Карточка ИБ + действия + аудит |
