# Автомат состояний

## Черновик (bot_sessions)

Мастер оформления хранится в `bot_sessions` до нажатия «Отправить».

`choose_zone` → `choose_time` → `choose_date` → `enter_guest_name` → `enter_purpose` → `confirm` → submit.

## Заявка (requests.status)

| Из | В | Кто |
|----|---|-----|
| — | pending | Инициатор (submit) |
| pending | approved / rejected / clarification | admin, tech_admin |
| pending | cancelled | Инициатор |
| clarification | pending | Инициатор (ответ) |
| clarification | cancelled | Инициатор |
| approved / rejected | closed | admin, tech_admin |

Терминальные: `cancelled`, `closed`.
