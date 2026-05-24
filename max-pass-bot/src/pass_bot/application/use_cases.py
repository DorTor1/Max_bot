from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pass_bot.domain.entities import RequestEntity, UserEntity
from pass_bot.domain.enums import (
    AuditEventType,
    RejectReason,
    RequestStatus,
    Role,
    VisitTime,
)
from pass_bot.domain.exceptions import Conflict, Forbidden, NotFound, ValidationError
from pass_bot.domain.repositories import (
    AuditRepository,
    BotSessionRepository,
    ClockPort,
    ConsentRepository,
    RequestRepository,
    UserRepository,
    ZoneRepository,
    audit_event,
)
from pass_bot.domain.services.request_state_machine import RequestStateMachine
from pass_bot.domain.services.role_policy import RolePolicy
from pass_bot.domain.value_objects import GuestName, Purpose, VisitDate


@dataclass
class Services:
    users: UserRepository
    consent: ConsentRepository
    zones: ZoneRepository
    requests: RequestRepository
    audit: AuditRepository
    sessions: BotSessionRepository
    clock: ClockPort
    consent_version: str
    state_machine: RequestStateMachine = RequestStateMachine()


class RecordConsent:
    def __init__(self, svc: Services) -> None:
        self._svc = svc

    def execute(self, actor: UserEntity) -> None:
        if self._svc.consent.has_consent(actor.id, self._svc.consent_version):
            return
        now = self._svc.clock.now()
        self._svc.consent.record(actor, self._svc.consent_version, accepted_at=now)
        self._svc.audit.append(
            audit_event(
                request_id=None,
                event_type=AuditEventType.CONSENT_ACCEPTED,
                actor=actor,
                payload={"version": self._svc.consent_version},
                now=now,
            )
        )


class SubmitRequest:
    def __init__(self, svc: Services) -> None:
        self._svc = svc

    def execute(
        self,
        actor: UserEntity,
        *,
        guest_full_name: str,
        visit_date: str,
        visit_time: VisitTime,
        zone_id: str,
        purpose: str,
    ) -> RequestEntity:
        if not self._svc.consent.has_consent(actor.id, self._svc.consent_version):
            raise Forbidden("Требуется согласие на обработку данных")

        guest = GuestName(guest_full_name)
        visit = VisitDate.from_iso(visit_date, today=self._svc.clock.today())
        purp = Purpose(purpose)
        zone = self._svc.zones.get(zone_id)
        if zone is None:
            raise ValidationError("zone_id", "Неизвестная зона")

        number = self._svc.requests.allocate_number(self._svc.clock.today().year)
        now = self._svc.clock.now()
        req = RequestEntity.create_pending(
            number=number,
            guest_full_name=guest.value,
            visit_date=visit.value,
            visit_time=visit_time,
            zone=zone,
            purpose=purp.value,
            initiator=actor,
            now=now,
        )
        self._svc.requests.save(req)
        self._svc.audit.append(
            audit_event(
                request_id=req.id,
                event_type=AuditEventType.SUBMITTED,
                actor=actor,
                payload={"number": number},
                now=now,
            )
        )
        self._svc.sessions.delete(actor.max_user_id)
        return req


class CancelRequest:
    def __init__(self, svc: Services) -> None:
        self._svc = svc

    def execute(self, actor: UserEntity, request_id: UUID) -> RequestEntity:
        req = self._require_request(request_id)
        if req.initiator_max_id != actor.max_user_id:
            raise Forbidden("Только инициатор")
        self._svc.state_machine.ensure_transition(
            req.status,
            RequestStatus.CANCELLED,
            role=actor.role,
            is_initiator=True,
        )
        now = self._svc.clock.now()
        req.status = RequestStatus.CANCELLED
        req.updated_at = now
        self._svc.requests.save(req)
        self._svc.audit.append(
            audit_event(
                request_id=req.id,
                event_type=AuditEventType.CANCELLED,
                actor=actor,
                now=now,
            )
        )
        return req

    def _require_request(self, request_id: UUID) -> RequestEntity:
        req = self._svc.requests.get(request_id)
        if req is None:
            raise NotFound("Заявка не найдена")
        return req


class AnswerClarification(CancelRequest):
    def execute(self, actor: UserEntity, request_id: UUID, answer: str) -> RequestEntity:
        req = self._require_request(request_id)
        if req.initiator_max_id != actor.max_user_id:
            raise Forbidden("Только инициатор")
        if req.status != RequestStatus.CLARIFICATION:
            raise Conflict("Ответ возможен только при статусе «уточнение»")
        text = answer.strip()
        if not text:
            raise ValidationError("answer", "Введите ответ")
        if len(text) > 2000:
            raise ValidationError("answer", "Максимум 2000 символов")

        self._svc.state_machine.ensure_transition(
            req.status,
            RequestStatus.PENDING,
            role=actor.role,
            is_initiator=True,
        )
        now = self._svc.clock.now()
        req.clarification_answer = text
        req.status = RequestStatus.PENDING
        req.updated_at = now
        self._svc.requests.save(req)
        self._svc.audit.append(
            audit_event(
                request_id=req.id,
                event_type=AuditEventType.CLARIFICATION_ANSWERED,
                actor=actor,
                now=now,
            )
        )
        return req


class AdminApprove:
    def __init__(self, svc: Services) -> None:
        self._svc = svc

    def execute(
        self, actor: UserEntity, request_id: UUID, comment: str | None = None
    ) -> RequestEntity:
        RolePolicy.require_admin(actor)
        req = self._get_pending(request_id)
        self._svc.state_machine.ensure_transition(
            req.status,
            RequestStatus.APPROVED,
            role=actor.role,
            is_initiator=False,
        )
        now = self._svc.clock.now()
        req.status = RequestStatus.APPROVED
        req.decision_by_id = actor.max_user_id
        req.decision_by_name = actor.display_name
        req.decision_comment = comment
        req.updated_at = now
        self._svc.requests.save(req)
        self._svc.audit.append(
            audit_event(
                request_id=req.id,
                event_type=AuditEventType.APPROVED,
                actor=actor,
                now=now,
            )
        )
        return req

    def _get_pending(self, request_id: UUID) -> RequestEntity:
        req = self._svc.requests.get(request_id)
        if req is None:
            raise NotFound("Заявка не найдена")
        if req.status != RequestStatus.PENDING:
            raise Conflict("Доступно только в статусе «на рассмотрении»")
        return req


class AdminReject(AdminApprove):
    def execute(
        self,
        actor: UserEntity,
        request_id: UUID,
        reason: RejectReason,
        comment: str | None = None,
    ) -> RequestEntity:
        RolePolicy.require_admin(actor)
        req = self._get_pending(request_id)
        self._svc.state_machine.ensure_transition(
            req.status,
            RequestStatus.REJECTED,
            role=actor.role,
            is_initiator=False,
        )
        now = self._svc.clock.now()
        req.status = RequestStatus.REJECTED
        req.decision_by_id = actor.max_user_id
        req.decision_by_name = actor.display_name
        req.decision_comment = comment
        req.reject_reason = reason
        req.updated_at = now
        self._svc.requests.save(req)
        self._svc.audit.append(
            audit_event(
                request_id=req.id,
                event_type=AuditEventType.REJECTED,
                actor=actor,
                payload={"reasonCode": reason.value},
                now=now,
            )
        )
        return req


class AdminClarify(AdminApprove):
    def execute(
        self, actor: UserEntity, request_id: UUID, question: str
    ) -> RequestEntity:
        RolePolicy.require_admin(actor)
        req = self._get_pending(request_id)
        q = question.strip()
        if len(q) < 3:
            raise ValidationError("question", "Минимум 3 символа")
        if len(q) > 2000:
            raise ValidationError("question", "Максимум 2000 символов")

        self._svc.state_machine.ensure_transition(
            req.status,
            RequestStatus.CLARIFICATION,
            role=actor.role,
            is_initiator=False,
        )
        now = self._svc.clock.now()
        req.status = RequestStatus.CLARIFICATION
        req.clarification_question = q
        req.updated_at = now
        self._svc.requests.save(req)
        self._svc.audit.append(
            audit_event(
                request_id=req.id,
                event_type=AuditEventType.CLARIFICATION_REQUESTED,
                actor=actor,
                payload={"preview": q[:80]},
                now=now,
            )
        )
        return req


class AdminClose(AdminApprove):
    def execute(self, actor: UserEntity, request_id: UUID) -> RequestEntity:
        RolePolicy.require_admin(actor)
        req = self._svc.requests.get(request_id)
        if req is None:
            raise NotFound("Заявка не найдена")
        if req.status not in (RequestStatus.APPROVED, RequestStatus.REJECTED):
            raise Conflict("Закрыть можно только одобренные или отклонённые")

        self._svc.state_machine.ensure_transition(
            req.status,
            RequestStatus.CLOSED,
            role=actor.role,
            is_initiator=False,
        )
        now = self._svc.clock.now()
        req.status = RequestStatus.CLOSED
        req.updated_at = now
        self._svc.requests.save(req)
        self._svc.audit.append(
            audit_event(
                request_id=req.id,
                event_type=AuditEventType.CLOSED,
                actor=actor,
                now=now,
            )
        )
        return req


class SetUserRole:
    def __init__(self, svc: Services) -> None:
        self._svc = svc

    def execute(self, actor: UserEntity, target_max_id: str, role: Role) -> UserEntity:
        RolePolicy.require_tech_admin(actor)
        if role == Role.TECH_ADMIN and actor.max_user_id != target_max_id:
            pass
        return self._svc.users.set_role(target_max_id, role)
