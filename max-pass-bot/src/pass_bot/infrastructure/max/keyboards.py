from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from pass_bot.domain.entities import RequestEntity, ZoneEntity
from pass_bot.domain.enums import RejectReason, RequestStatus, VisitTime
from pass_bot.infrastructure.max import payloads as pl


def consent_keyboard(version: str) -> InlineKeyboardBuilder:
    b = InlineKeyboardBuilder()
    b.row(
        CallbackButton(text="Принимаю", payload=pl.encode("consent", "accept")),
        CallbackButton(text="Отказ", payload=pl.encode("consent", "decline")),
    )
    return b


def main_menu_keyboard(*, is_admin: bool, is_tech: bool) -> InlineKeyboardBuilder:
    b = InlineKeyboardBuilder()
    b.row(CallbackButton(text="Новая заявка", payload=pl.encode("menu", "new")))
    b.row(CallbackButton(text="Мои заявки", payload=pl.encode("menu", "mine")))
    if is_admin or is_tech:
        b.row(CallbackButton(text="Очередь ИБ", payload=pl.encode("menu", "queue")))
    if is_tech:
        b.row(
            CallbackButton(
                text="Назначить admin",
                payload=pl.encode("tech", "setadmin"),
            )
        )
    return b


def zones_keyboard(zones: list[ZoneEntity]) -> InlineKeyboardBuilder:
    b = InlineKeyboardBuilder()
    for z in zones:
        b.row(CallbackButton(text=z.title, payload=pl.encode("zone", z.id)))
    b.row(CallbackButton(text="Отмена", payload=pl.encode("wizard", "cancel")))
    return b


def visit_time_keyboard() -> InlineKeyboardBuilder:
    b = InlineKeyboardBuilder()
    b.row(
        CallbackButton(text="Утро", payload=pl.encode("time", VisitTime.MORNING.value)),
        CallbackButton(text="День", payload=pl.encode("time", VisitTime.DAY.value)),
        CallbackButton(text="Вечер", payload=pl.encode("time", VisitTime.EVENING.value)),
    )
    b.row(CallbackButton(text="Назад", payload=pl.encode("wizard", "back_zone")))
    return b


def visit_date_keyboard(today_iso: str, tomorrow_iso: str, day_after_iso: str) -> InlineKeyboardBuilder:
    b = InlineKeyboardBuilder()
    b.row(
        CallbackButton(text="Сегодня", payload=pl.encode("date", today_iso)),
        CallbackButton(text="Завтра", payload=pl.encode("date", tomorrow_iso)),
    )
    b.row(CallbackButton(text="Послезавтра", payload=pl.encode("date", day_after_iso)))
    b.row(CallbackButton(text="Назад", payload=pl.encode("wizard", "back_time")))
    return b


def confirm_keyboard() -> InlineKeyboardBuilder:
    b = InlineKeyboardBuilder()
    b.row(
        CallbackButton(text="Отправить", payload=pl.encode("wizard", "submit")),
        CallbackButton(text="Изменить зону", payload=pl.encode("wizard", "edit_zone")),
    )
    b.row(CallbackButton(text="Отмена", payload=pl.encode("wizard", "cancel")))
    return b


def request_card_keyboard(req: RequestEntity, *, viewer_is_initiator: bool) -> InlineKeyboardBuilder:
    b = InlineKeyboardBuilder()
    rid = str(req.id)
    if viewer_is_initiator:
        if req.status in (RequestStatus.PENDING, RequestStatus.CLARIFICATION):
            b.row(CallbackButton(text="Отменить", payload=pl.encode("req", f"cancel:{rid}")))
        if req.status == RequestStatus.CLARIFICATION:
            b.row(
                CallbackButton(
                    text="Ответить на уточнение",
                    payload=pl.encode("req", f"answer:{rid}"),
                )
            )
    if req.status == RequestStatus.PENDING:
        b.row(
            CallbackButton(text="Одобрить", payload=pl.encode("adm", f"ok:{rid}")),
            CallbackButton(text="Отклонить", payload=pl.encode("adm", f"rej:{rid}")),
        )
        b.row(CallbackButton(text="Уточнение", payload=pl.encode("adm", f"clar:{rid}")))
    if req.status in (RequestStatus.APPROVED, RequestStatus.REJECTED):
        b.row(CallbackButton(text="Закрыть", payload=pl.encode("adm", f"close:{rid}")))
    b.row(CallbackButton(text="В меню", payload=pl.encode("menu", "home")))
    return b


def reject_reason_keyboard(request_id: str) -> InlineKeyboardBuilder:
    b = InlineKeyboardBuilder()
    for reason in RejectReason:
        labels = {
            RejectReason.INVALID_DATA: "Неверные данные",
            RejectReason.SECURITY_POLICY: "Политика ИБ",
            RejectReason.DUPLICATE: "Дубликат",
            RejectReason.OTHER: "Другое",
        }
        b.row(
            CallbackButton(
                text=labels[reason],
                payload=pl.encode("rej", f"{request_id}:{reason.value}"),
            )
        )
    b.row(CallbackButton(text="Отмена", payload=pl.encode("menu", "queue")))
    return b
