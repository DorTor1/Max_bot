from __future__ import annotations

import logging
from datetime import timedelta
from uuid import UUID

from maxapi import Bot, Dispatcher, F
from maxapi.types import BotAdded, BotStarted, Command, MessageCallback, MessageCreated

from pass_bot.application.use_cases import (
    AdminApprove,
    AdminClarify,
    AdminClose,
    AdminReject,
    AnswerClarification,
    CancelRequest,
    RecordConsent,
    Services,
    SetUserRole,
    SubmitRequest,
)
from pass_bot.domain.entities import BotSessionEntity, UserEntity
from pass_bot.domain.enums import RejectReason, RequestStatus, Role, VisitTime, WizardStep
from pass_bot.domain.exceptions import Conflict, DomainError, Forbidden, NotFound, ValidationError
from pass_bot.domain.services.role_policy import RolePolicy
from pass_bot.infrastructure.config.settings import Settings
from pass_bot.infrastructure.max import payloads as pl
from pass_bot.infrastructure.max.async_db import run_db
from pass_bot.infrastructure.max.context_state import (
    PENDING_REJECT_ID,
    PENDING_REQUEST_ID,
    WAIT_ADMIN_QUESTION,
    WAIT_CLARIFY_ANSWER,
    WAIT_GUEST_NAME,
    WAIT_PURPOSE,
    WAIT_TECH_TARGET,
    WAITING,
)
from pass_bot.infrastructure.max.keyboards import (
    confirm_keyboard,
    consent_keyboard,
    main_menu_keyboard,
    reject_reason_keyboard,
    request_card_keyboard,
    visit_date_keyboard,
    visit_time_keyboard,
    zones_keyboard,
)
from pass_bot.infrastructure.max.texts import DISCLAIMER, GROUP_ONLY_PRIVATE, MAIN_MENU_ADMIN, MAIN_MENU_INITIATOR
from pass_bot.infrastructure.max.users import display_name, max_user_id
from pass_bot.domain.value_objects.visit_date import VisitDate

logger = logging.getLogger(__name__)

# Per-user pending text input (in-memory; survives only process lifetime)
_pending_text: dict[str, str] = {}


def register_handlers(dp: Dispatcher, bot: Bot, settings: Settings) -> None:
    @dp.bot_added()
    async def on_bot_added(event: BotAdded) -> None:
        await event.bot.send_message(
            chat_id=event.chat.chat_id,
            text=GROUP_ONLY_PRIVATE,
        )
        try:
            await event.bot.delete_me_from_chat(chat_id=event.chat.chat_id)
        except Exception:
            logger.warning("Could not leave group chat %s", event.chat.chat_id)

    async def _resolve_user(max_user: object) -> UserEntity:
        uid = max_user_id(max_user)  # type: ignore[arg-type]
        name = display_name(max_user)  # type: ignore[arg-type]

        def _load(svc: Services) -> UserEntity:
            return svc.users.upsert_from_max(uid, name, default_role=Role.INITIATOR)

        return await run_db(settings, _load)

    async def _has_consent(user: UserEntity) -> bool:
        def _check(svc: Services) -> bool:
            return svc.consent.has_consent(user.id, svc.consent_version)

        return await run_db(settings, _check)

    async def _send_consent(event: MessageCreated | BotStarted, user: UserEntity) -> None:
        text = DISCLAIMER.format(version=settings.consent_version)
        kb = consent_keyboard(settings.consent_version)
        if isinstance(event, MessageCreated):
            await event.message.answer(text=text, attachments=[kb.as_markup()])
        else:
            await event.bot.send_message(
                chat_id=event.chat_id,
                text=text,
                attachments=[kb.as_markup()],
            )

    async def _send_main_menu(event: MessageCreated, user: UserEntity) -> None:
        is_admin = user.role in (Role.ADMIN, Role.TECH_ADMIN)
        text = MAIN_MENU_ADMIN if is_admin else MAIN_MENU_INITIATOR
        kb = main_menu_keyboard(is_admin=is_admin, is_tech=user.role == Role.TECH_ADMIN)
        await event.message.answer(text=text, attachments=[kb.as_markup()])

    @dp.bot_started()
    async def on_start(event: BotStarted) -> None:
        user = await _resolve_user(event.user)
        if not await _has_consent(user):
            await _send_consent(event, user)  # type: ignore[arg-type]
            return
        await event.bot.send_message(
            chat_id=event.chat_id,
            text=MAIN_MENU_INITIATOR,
            attachments=[
                main_menu_keyboard(
                    is_admin=user.role in (Role.ADMIN, Role.TECH_ADMIN),
                    is_tech=user.role == Role.TECH_ADMIN,
                ).as_markup()
            ],
        )

    @dp.message_created(Command("start"))
    async def cmd_start(event: MessageCreated) -> None:
        sender = event.message.sender
        if sender is None:
            return
        user = await _resolve_user(sender)
        if not await _has_consent(user):
            await _send_consent(event, user)
            return
        await _send_main_menu(event, user)

    @dp.message_callback()
    async def on_callback(event: MessageCallback) -> None:
        action, arg = pl.decode(event.callback.payload or "")
        user = await _resolve_user(event.callback.user)
        await event.ack(notification="Принято")

        if action == "consent":
            await _handle_consent(event, user, arg)
        elif action == "menu":
            await _handle_menu(event, user, arg)
        elif action == "zone":
            await _handle_zone(event, user, arg)
        elif action == "time":
            await _handle_time(event, user, arg)
        elif action == "date":
            await _handle_date(event, user, arg)
        elif action == "wizard":
            await _handle_wizard(event, user, arg)
        elif action == "req":
            await _handle_request_action(event, user, arg)
        elif action == "adm":
            await _handle_admin_action(event, user, arg)
        elif action == "rej":
            await _handle_reject_reason(event, user, arg)
        elif action == "tech":
            await _handle_tech(event, user, arg)

    async def _handle_consent(event: MessageCallback, user: UserEntity, arg: str | None) -> None:
        if arg != "accept":
            if event.message:
                await event.message.answer("Без согласия сервис недоступен.")
            return

        def _record(svc: Services) -> None:
            RecordConsent(svc).execute(user)

        await run_db(settings, _record)
        if event.message:
            await event.message.answer(
                "Согласие зафиксировано в аудит-логе.",
                attachments=[
                    main_menu_keyboard(
                        is_admin=user.role in (Role.ADMIN, Role.TECH_ADMIN),
                        is_tech=user.role == Role.TECH_ADMIN,
                    ).as_markup()
                ],
            )

    async def _handle_menu(event: MessageCallback, user: UserEntity, arg: str | None) -> None:
        if not event.message:
            return
        if not await _has_consent(user):
            await event.message.answer("Сначала примите согласие: /start")
            return
        if arg == "new":
            await _start_wizard(event, user)
        elif arg == "mine":
            await _list_my_requests(event, user)
        elif arg == "queue":
            await _list_queue(event, user)
        elif arg == "home":
            await _send_main_menu_msg(event, user)

    async def _send_main_menu_msg(event: MessageCallback, user: UserEntity) -> None:
        if not event.message:
            return
        is_admin = user.role in (Role.ADMIN, Role.TECH_ADMIN)
        text = MAIN_MENU_ADMIN if is_admin else MAIN_MENU_INITIATOR
        kb = main_menu_keyboard(is_admin=is_admin, is_tech=user.role == Role.TECH_ADMIN)
        await event.message.answer(text=text, attachments=[kb.as_markup()])

    async def _start_wizard(event: MessageCallback, user: UserEntity) -> None:
        def _init(svc: Services) -> list:
            zones = svc.zones.list_all()
            svc.sessions.save(
                BotSessionEntity(
                    max_user_id=user.max_user_id,
                    step=WizardStep.CHOOSE_ZONE.value,
                    draft={},
                )
            )
            return zones

        zones = await run_db(settings, _init)
        if event.message:
            await event.message.answer(
                "Шаг 1/5. Выберите зону:",
                attachments=[zones_keyboard(zones).as_markup()],
            )

    async def _handle_zone(event: MessageCallback, user: UserEntity, zone_id: str | None) -> None:
        if not zone_id or not event.message:
            return

        def _save(svc: Services) -> None:
            sess = svc.sessions.get(user.max_user_id) or BotSessionEntity(
                max_user_id=user.max_user_id, step=WizardStep.CHOOSE_ZONE.value
            )
            sess.draft["zone_id"] = zone_id
            sess.step = WizardStep.CHOOSE_TIME.value
            svc.sessions.save(sess)

        await run_db(settings, _save)
        await event.message.answer(
            "Шаг 2/5. Время визита:",
            attachments=[visit_time_keyboard().as_markup()],
        )

    async def _handle_time(event: MessageCallback, user: UserEntity, time_val: str | None) -> None:
        if not time_val or not event.message:
            return

        def _save(svc: Services) -> tuple[str, str, str]:
            sess = svc.sessions.get(user.max_user_id)
            if sess is None:
                raise Conflict("Сессия мастера не найдена")
            sess.draft["visit_time"] = time_val
            sess.step = WizardStep.CHOOSE_DATE.value
            svc.sessions.save(sess)
            t = svc.clock.today()
            return (
                t.isoformat(),
                (t + timedelta(days=1)).isoformat(),
                (t + timedelta(days=2)).isoformat(),
            )

        today, tomorrow, day_after = await run_db(settings, _save)
        await event.message.answer(
            "Шаг 3/5. Дата визита:",
            attachments=[visit_date_keyboard(today, tomorrow, day_after).as_markup()],
        )

    async def _handle_date(event: MessageCallback, user: UserEntity, date_iso: str | None) -> None:
        if not date_iso or not event.message:
            return

        def _save(svc: Services) -> None:
            sess = svc.sessions.get(user.max_user_id)
            if sess is None:
                raise Conflict("Сессия мастера не найдена")
            VisitDate.from_iso(date_iso, today=svc.clock.today())
            sess.draft["visit_date"] = date_iso
            sess.step = WizardStep.ENTER_GUEST_NAME.value
            sess.draft[WAITING] = WAIT_GUEST_NAME
            svc.sessions.save(sess)

        try:
            await run_db(settings, _save)
        except ValidationError as e:
            await event.message.answer(e.message)
            return
        _pending_text[user.max_user_id] = WAIT_GUEST_NAME
        await event.message.answer("Шаг 4/5. Введите ФИО гостя текстом:")

    async def _handle_wizard(event: MessageCallback, user: UserEntity, arg: str | None) -> None:
        if not event.message:
            return
        if arg == "cancel":

            def _clear(svc: Services) -> None:
                svc.sessions.delete(user.max_user_id)

            await run_db(settings, _clear)
            _pending_text.pop(user.max_user_id, None)
            await _send_main_menu_msg(event, user)
        elif arg == "submit":
            await _submit_wizard(event, user)
        elif arg == "edit_zone" or arg == "back_zone":
            await _start_wizard(event, user)
        elif arg == "back_time":

            def _back(svc: Services) -> None:
                sess = svc.sessions.get(user.max_user_id)
                if sess:
                    sess.step = WizardStep.CHOOSE_TIME.value
                    svc.sessions.save(sess)

            await run_db(settings, _back)
            await event.message.answer(
                "Шаг 2/5. Время визита:",
                attachments=[visit_time_keyboard().as_markup()],
            )

    async def _submit_wizard(event: MessageCallback, user: UserEntity) -> None:
        def _submit(svc: Services):
            sess = svc.sessions.get(user.max_user_id)
            if sess is None:
                raise Conflict("Нет черновика")
            d = sess.draft
            return SubmitRequest(svc).execute(
                user,
                guest_full_name=d["guest_full_name"],
                visit_date=d["visit_date"],
                visit_time=VisitTime(d["visit_time"]),
                zone_id=d["zone_id"],
                purpose=d["purpose"],
            )

        try:
            req = await run_db(settings, _submit)
            _pending_text.pop(user.max_user_id, None)
            if event.message:
                await event.message.answer(
                    f"Заявка {req.number} отправлена на рассмотрение.\n"
                    f"Гость: {req.guest_full_name}\n"
                    f"Дата: {req.visit_date} ({req.visit_time.value})\n"
                    f"Зона: {req.zone_title}",
                    attachments=[
                        main_menu_keyboard(
                            is_admin=user.role in (Role.ADMIN, Role.TECH_ADMIN),
                            is_tech=user.role == Role.TECH_ADMIN,
                        ).as_markup()
                    ],
                )
        except DomainError as e:
            if event.message:
                await event.message.answer(str(e))

    async def _show_confirm(event: MessageCallback, user: UserEntity) -> None:
        def _get(svc: Services) -> str:
            sess = svc.sessions.get(user.max_user_id)
            if sess is None:
                return ""
            d = sess.draft
            zone = svc.zones.get(d.get("zone_id", ""))
            return (
                f"Проверьте заявку:\n"
                f"Зона: {zone.title if zone else d.get('zone_id')}\n"
                f"Время: {d.get('visit_time')}\n"
                f"Дата: {d.get('visit_date')}\n"
                f"ФИО: {d.get('guest_full_name')}\n"
                f"Цель: {d.get('purpose')}"
            )

        text = await run_db(settings, _get)
        if event.message:
            await event.message.answer(text, attachments=[confirm_keyboard().as_markup()])

    async def _list_my_requests(event: MessageCallback, user: UserEntity) -> None:
        def _list(svc: Services):
            return svc.requests.list_by_initiator(user.id)

        reqs = await run_db(settings, _list)
        if not event.message:
            return
        if not reqs:
            await event.message.answer("У вас пока нет заявок.")
            return
        for r in reqs[:10]:
            await event.message.answer(
                _format_request(r),
                attachments=[
                    request_card_keyboard(
                        r, viewer_is_initiator=r.initiator_max_id == user.max_user_id
                    ).as_markup()
                ],
            )

    async def _list_queue(event: MessageCallback, user: UserEntity) -> None:
        try:
            RolePolicy.require_admin(user)
        except Forbidden:
            if event.message:
                await event.message.answer("Нужна роль администратора ИБ.")
            return

        def _list(svc: Services):
            return svc.requests.list_by_status(RequestStatus.PENDING)

        reqs = await run_db(settings, _list)
        if not event.message:
            return
        if not reqs:
            await event.message.answer("Очередь пуста.")
            return
        for r in reqs[:15]:
            await event.message.answer(
                _format_request(r),
                attachments=[request_card_keyboard(r, viewer_is_initiator=False).as_markup()],
            )

    async def _handle_request_action(
        event: MessageCallback, user: UserEntity, arg: str | None
    ) -> None:
        if not arg or not event.message:
            return
        kind, rid = arg.split(":", 1)
        req_id = UUID(rid)
        if kind == "cancel":

            def _cancel(svc: Services):
                return CancelRequest(svc).execute(user, req_id)

            try:
                r = await run_db(settings, _cancel)
                await event.message.answer(f"Заявка {r.number} отменена.")
            except DomainError as e:
                await event.message.answer(str(e))
        elif kind == "answer":
            _pending_text[user.max_user_id] = WAIT_CLARIFY_ANSWER

            def _mark(svc: Services) -> None:
                sess = svc.sessions.get(user.max_user_id) or BotSessionEntity(
                    max_user_id=user.max_user_id, step="answer", draft={}
                )
                sess.draft[PENDING_REQUEST_ID] = rid
                sess.draft[WAITING] = WAIT_CLARIFY_ANSWER
                svc.sessions.save(sess)

            await run_db(settings, _mark)
            await event.message.answer("Введите ответ на уточнение текстом:")

    async def _handle_admin_action(
        event: MessageCallback, user: UserEntity, arg: str | None
    ) -> None:
        if not arg or not event.message:
            return
        kind, rid = arg.split(":", 1)
        req_id = UUID(rid)
        if kind == "ok":

            def _ok(svc: Services):
                return AdminApprove(svc).execute(user, req_id)

            try:
                r = await run_db(settings, _ok)
                await event.message.answer(f"Заявка {r.number} одобрена.")
            except DomainError as e:
                await event.message.answer(str(e))
        elif kind == "rej":
            await event.message.answer(
                "Выберите причину отклонения:",
                attachments=[reject_reason_keyboard(rid).as_markup()],
            )
        elif kind == "clar":
            _pending_text[user.max_user_id] = WAIT_ADMIN_QUESTION

            def _mark(svc: Services) -> None:
                sess = svc.sessions.get(user.max_user_id) or BotSessionEntity(
                    max_user_id=user.max_user_id, step="admin", draft={}
                )
                sess.draft[PENDING_REQUEST_ID] = rid
                sess.draft[WAITING] = WAIT_ADMIN_QUESTION
                svc.sessions.save(sess)

            await run_db(settings, _mark)
            await event.message.answer("Введите вопрос для инициатора:")
        elif kind == "close":

            def _close(svc: Services):
                return AdminClose(svc).execute(user, req_id)

            try:
                r = await run_db(settings, _close)
                await event.message.answer(f"Заявка {r.number} закрыта.")
            except DomainError as e:
                await event.message.answer(str(e))

    async def _handle_reject_reason(
        event: MessageCallback, user: UserEntity, arg: str | None
    ) -> None:
        if not arg or not event.message:
            return
        rid, reason_code = arg.split(":", 1)
        req_id = UUID(rid)
        reason = RejectReason(reason_code)

        def _reject(svc: Services):
            return AdminReject(svc).execute(user, req_id, reason)

        try:
            r = await run_db(settings, _reject)
            await event.message.answer(f"Заявка {r.number} отклонена.")
        except DomainError as e:
            await event.message.answer(str(e))

    async def _handle_tech(event: MessageCallback, user: UserEntity, arg: str | None) -> None:
        if arg == "setadmin":
            try:
                RolePolicy.require_tech_admin(user)
            except Forbidden:
                if event.message:
                    await event.message.answer("Только технический администратор.")
                return
            _pending_text[user.max_user_id] = WAIT_TECH_TARGET
            if event.message:
                await event.message.answer(
                    "Отправьте MAX user_id пользователя, которому назначить роль admin:"
                )

    @dp.message_created(F.message.body.text)
    async def on_text(event: MessageCreated) -> None:
        sender = event.message.sender
        if sender is None or not event.message.body.text:
            return
        user = await _resolve_user(sender)
        if not await _has_consent(user):
            await _send_consent(event, user)
            return

        wait = _pending_text.get(user.max_user_id)
        text = event.message.body.text.strip()
        if not wait:
            await event.message.answer("Используйте кнопки меню. Команда: /start")
            return

        if wait == WAIT_GUEST_NAME:
            await _on_guest_name(event, user, text)
        elif wait == WAIT_PURPOSE:
            await _on_purpose(event, user, text)
        elif wait == WAIT_CLARIFY_ANSWER:
            await _on_clarify_answer(event, user, text)
        elif wait == WAIT_ADMIN_QUESTION:
            await _on_admin_question(event, user, text)
        elif wait == WAIT_TECH_TARGET:
            await _on_tech_set_admin(event, user, text)

    async def _on_guest_name(event: MessageCreated, user: UserEntity, text: str) -> None:
        from pass_bot.domain.value_objects import GuestName

        try:
            GuestName(text)
        except ValidationError as e:
            await event.message.answer(e.message)
            return

        def _save(svc: Services) -> None:
            sess = svc.sessions.get(user.max_user_id)
            if sess is None:
                raise Conflict("Сессия не найдена")
            sess.draft["guest_full_name"] = text
            sess.step = WizardStep.ENTER_PURPOSE.value
            sess.draft[WAITING] = WAIT_PURPOSE
            svc.sessions.save(sess)

        await run_db(settings, _save)
        _pending_text[user.max_user_id] = WAIT_PURPOSE
        await event.message.answer("Шаг 5/5. Введите цель визита текстом:")

    async def _on_purpose(event: MessageCreated, user: UserEntity, text: str) -> None:
        from pass_bot.domain.value_objects import Purpose

        try:
            Purpose(text)
        except ValidationError as e:
            await event.message.answer(e.message)
            return

        def _save(svc: Services) -> None:
            sess = svc.sessions.get(user.max_user_id)
            if sess is None:
                raise Conflict("Сессия не найдена")
            sess.draft["purpose"] = text
            sess.step = WizardStep.CONFIRM.value
            sess.draft.pop(WAITING, None)
            svc.sessions.save(sess)

        await run_db(settings, _save)
        _pending_text.pop(user.max_user_id, None)

        def _summary(svc: Services) -> str:
            sess = svc.sessions.get(user.max_user_id)
            d = sess.draft if sess else {}
            zone = svc.zones.get(d.get("zone_id", ""))
            return (
                f"Проверьте заявку:\n"
                f"Зона: {zone.title if zone else '?'}\n"
                f"Время: {d.get('visit_time')}\n"
                f"Дата: {d.get('visit_date')}\n"
                f"ФИО: {d.get('guest_full_name')}\n"
                f"Цель: {d.get('purpose')}"
            )

        summary = await run_db(settings, _summary)
        await event.message.answer(summary, attachments=[confirm_keyboard().as_markup()])

    async def _on_clarify_answer(event: MessageCreated, user: UserEntity, text: str) -> None:

        def _answer(svc: Services):
            sess = svc.sessions.get(user.max_user_id)
            rid = UUID(sess.draft[PENDING_REQUEST_ID]) if sess else None
            if rid is None:
                raise NotFound()
            return AnswerClarification(svc).execute(user, rid, text)

        try:
            r = await run_db(settings, _answer)
            _pending_text.pop(user.max_user_id, None)
            await event.message.answer(f"Ответ отправлен. Заявка {r.number} снова на рассмотрении.")
        except DomainError as e:
            await event.message.answer(str(e))

    async def _on_admin_question(event: MessageCreated, user: UserEntity, text: str) -> None:

        def _clarify(svc: Services):
            sess = svc.sessions.get(user.max_user_id)
            rid = UUID(sess.draft[PENDING_REQUEST_ID]) if sess else None
            if rid is None:
                raise NotFound()
            return AdminClarify(svc).execute(user, rid, text)

        try:
            r = await run_db(settings, _clarify)
            _pending_text.pop(user.max_user_id, None)
            await event.message.answer(f"Запрошено уточнение по заявке {r.number}.")
        except DomainError as e:
            await event.message.answer(str(e))

    async def _on_tech_set_admin(event: MessageCreated, user: UserEntity, target_id: str) -> None:

        def _set(svc: Services):
            SetUserRole(svc).execute(user, target_id.strip(), Role.ADMIN)

        try:
            await run_db(settings, _set)
            _pending_text.pop(user.max_user_id, None)
            await event.message.answer(f"Пользователю {target_id} назначена роль admin.")
        except DomainError as e:
            await event.message.answer(str(e))


def _format_request(r) -> str:
    status_labels = {
        RequestStatus.PENDING: "На рассмотрении",
        RequestStatus.APPROVED: "Одобрено",
        RequestStatus.REJECTED: "Отклонено",
        RequestStatus.CLARIFICATION: "Требуется уточнение",
        RequestStatus.CANCELLED: "Отменена",
        RequestStatus.CLOSED: "Закрыта",
    }
    lines = [
        f"{r.number} — {status_labels.get(r.status, r.status.value)}",
        f"Гость: {r.guest_full_name}",
        f"Дата: {r.visit_date} ({r.visit_time.value})",
        f"Зона: {r.zone_title}",
        f"Цель: {r.purpose[:80]}{'…' if len(r.purpose) > 80 else ''}",
    ]
    if r.clarification_question:
        lines.append(f"Вопрос ИБ: {r.clarification_question}")
    return "\n".join(lines)
