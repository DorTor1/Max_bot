# Электронное бюро пропусков — чат-бот MAX

Нативный чат-бот для мессенджера **MAX** (разовый гостевой пропуск). Доменная логика и статусы заявок согласованы с mini-app в корне репозитория ([`openapi.yaml`](../openapi.yaml)).

## Требования

- Python 3.11+
- PostgreSQL 16 (или `docker compose up -d`)
- Токен бота из [панели интеграции MAX](https://dev.max.ru)
- Ник бота по шаблону `idИНН_bot`

## Быстрый старт

```bash
cd max-pass-bot
cp .env.example .env
# Укажите BOT_TOKEN в .env

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

docker compose up -d
alembic upgrade head   # или: таблицы создаются при первом запуске через bootstrap

# Разработка (long polling)
pass-bot-poll
```

## Webhook (production)

MAX принимает webhook на портах **80, 8080, 443, 8443** или **16384–32383**.

```bash
# .env
BOT_MODE=webhook
WEBHOOK_PUBLIC_URL=https://your-host/max/webhook
WEBHOOK_SECRET=your_secret_5_to_256_chars
WEBHOOK_PATH=/max/webhook
WEBHOOK_PORT=8080

pass-bot-webhook
```

Проверка заголовка `X-Max-Bot-Api-Secret` выполняется автоматически (тот же `WEBHOOK_SECRET` передаётся в `subscribe_webhook`).

Дополнительно: `GET /health` → `{"status":"ok"}`.

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен из панели MAX |
| `DATABASE_URL` | PostgreSQL URL |
| `CONSENT_VERSION` | Версия текста согласия (напр. `2026-05-1`) |
| `TECH_ADMIN_MAX_IDS` | MAX user_id тех. админов через запятую |
| `WEBHOOK_*` | Параметры webhook-режима |

## Роли

| Роль | Возможности |
|------|-------------|
| `initiator` | Мастер заявки, свои заявки, отмена до решения ИБ |
| `admin` | Очередь, одобрение/отклонение/уточнение/закрытие |
| `tech_admin` | То же + назначение `admin` по MAX user_id |

Роли задаются **только в БД** (seed `TECH_ADMIN_MAX_IDS` или команда тех. админа). Секретных фраз нет.

## Приватность MAX

В кабинете бота включите запрет добавления в группы. При добавлении в группу бот отправляет предупреждение и пытается покинуть чат.

## Архитектура

```
src/pass_bot/
  domain/          # сущности, value objects, state machine
  application/     # use cases
  infrastructure/  # SQLAlchemy, maxapi handlers
  interfaces/      # FastAPI webhook
```

Документация: [`docs/state-machine.md`](docs/state-machine.md), [`docs/bot-flow.md`](docs/bot-flow.md).

## Тесты

```bash
pytest
```

## Smoke-сценарий

1. `/start` → принять согласие.
2. «Новая заявка» → зона → время → дата → ФИО → цель → «Отправить».
3. Проверить номер `GP-YYYY-NNNNNN` и статус «На рассмотрении».
4. Под учёткой admin: «Очередь ИБ» → одобрить → закрыть.
