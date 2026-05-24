from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from pass_bot.domain.entities import (
    AuditEventEntity,
    BotSessionEntity,
    RequestEntity,
    UserEntity,
    ZoneEntity,
)
from pass_bot.domain.enums import RejectReason, RequestStatus, Role, VisitTime
from pass_bot.domain.repositories import (
    AuditRepository,
    BotSessionRepository,
    ClockPort,
    ConsentRepository,
    RequestRepository,
    UserRepository,
    ZoneRepository,
)
from pass_bot.infrastructure.persistence.models import (
    AuditEventModel,
    BotSessionModel,
    ConsentRecordModel,
    RejectReasonEnum,
    RequestModel,
    RequestNumberSeqModel,
    RequestStatusEnum,
    RoleEnum,
    UserModel,
    VisitTimeEnum,
    ZoneModel,
)


class SystemClock(ClockPort):
    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def today(self) -> date:
        return self.now().date()


def _role_from_db(r: RoleEnum) -> Role:
    return Role(r.value)


def _role_to_db(r: Role) -> RoleEnum:
    return RoleEnum(r.value)


def _user_entity(m: UserModel) -> UserEntity:
    return UserEntity(
        id=m.id,
        max_user_id=m.max_user_id,
        display_name=m.display_name,
        role=_role_from_db(m.role),
        is_active=m.is_active,
    )


def _status_from_db(s: RequestStatusEnum) -> RequestStatus:
    return RequestStatus(s.value)


def _status_to_db(s: RequestStatus) -> RequestStatusEnum:
    return RequestStatusEnum(s.value)


def _visit_from_db(v: VisitTimeEnum) -> VisitTime:
    return VisitTime(v.value)


def _visit_to_db(v: VisitTime) -> VisitTimeEnum:
    return VisitTimeEnum(v.value)


class SqlUserRepository(UserRepository):
    def __init__(self, session: Session, tech_admin_ids: list[str]) -> None:
        self._s = session
        self._tech_admin_ids = tech_admin_ids

    def get_by_max_id(self, max_user_id: str) -> UserEntity | None:
        m = self._s.scalar(select(UserModel).where(UserModel.max_user_id == max_user_id))
        return _user_entity(m) if m else None

    def upsert_from_max(
        self, max_user_id: str, display_name: str, *, default_role: Role
    ) -> UserEntity:
        m = self._s.scalar(select(UserModel).where(UserModel.max_user_id == max_user_id))
        role = default_role
        if max_user_id in self._tech_admin_ids:
            role = Role.TECH_ADMIN
        if m is None:
            m = UserModel(
                id=uuid4(),
                max_user_id=max_user_id,
                display_name=display_name,
                role=_role_to_db(role),
            )
            self._s.add(m)
        else:
            m.display_name = display_name
        self._s.flush()
        return _user_entity(m)

    def set_role(self, max_user_id: str, role: Role) -> UserEntity:
        m = self._s.scalar(select(UserModel).where(UserModel.max_user_id == max_user_id))
        if m is None:
            raise ValueError(f"User {max_user_id} not found")
        m.role = _role_to_db(role)
        self._s.flush()
        return _user_entity(m)

    def list_by_role(self, role: Role) -> list[UserEntity]:
        rows = self._s.scalars(
            select(UserModel).where(UserModel.role == _role_to_db(role))
        ).all()
        return [_user_entity(r) for r in rows]


class SqlConsentRepository(ConsentRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def has_consent(self, user_id: UUID, doc_version: str) -> bool:
        row = self._s.scalar(
            select(ConsentRecordModel).where(
                ConsentRecordModel.user_id == user_id,
                ConsentRecordModel.doc_version == doc_version,
            )
        )
        return row is not None

    def record(
        self, user: UserEntity, doc_version: str, *, accepted_at: datetime
    ) -> None:
        if self.has_consent(user.id, doc_version):
            return
        self._s.add(
            ConsentRecordModel(
                id=uuid4(),
                user_id=user.id,
                doc_version=doc_version,
                accepted_at=accepted_at,
                max_user_id=user.max_user_id,
                display_name=user.display_name,
            )
        )


class SqlZoneRepository(ZoneRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def list_all(self) -> list[ZoneEntity]:
        rows = self._s.scalars(select(ZoneModel).order_by(ZoneModel.sort_order)).all()
        return [ZoneEntity(id=r.id, title=r.title, sort_order=r.sort_order) for r in rows]

    def get(self, zone_id: str) -> ZoneEntity | None:
        r = self._s.get(ZoneModel, zone_id)
        return ZoneEntity(id=r.id, title=r.title, sort_order=r.sort_order) if r else None


class SqlRequestRepository(RequestRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def _to_entity(self, m: RequestModel) -> RequestEntity:
        initiator = m.initiator
        rr = RejectReason(m.reject_reason.value) if m.reject_reason else None
        return RequestEntity(
            id=m.id,
            number=m.number,
            guest_full_name=m.guest_full_name,
            visit_date=m.visit_date,
            visit_time=_visit_from_db(m.visit_time),
            zone_id=m.zone_id,
            zone_title=m.zone.title if m.zone else m.zone_id,
            purpose=m.purpose,
            status=_status_from_db(m.status),
            initiator_user_id=m.initiator_user_id,
            initiator_max_id=initiator.max_user_id,
            initiator_display_name=initiator.display_name,
            created_at=m.created_at,
            updated_at=m.updated_at,
            decision_by_id=m.decision_by_id,
            decision_by_name=m.decision_by_name,
            decision_comment=m.decision_comment,
            reject_reason=rr,
            clarification_question=m.clarification_question,
            clarification_answer=m.clarification_answer,
        )

    def save(self, request: RequestEntity) -> None:
        m = self._s.get(RequestModel, request.id)
        if m is None:
            m = RequestModel(
                id=request.id,
                number=request.number,
                guest_full_name=request.guest_full_name,
                visit_date=request.visit_date,
                visit_time=_visit_to_db(request.visit_time),
                zone_id=request.zone_id,
                purpose=request.purpose,
                status=_status_to_db(request.status),
                initiator_user_id=request.initiator_user_id,
            )
            self._s.add(m)
        m.number = request.number
        m.guest_full_name = request.guest_full_name
        m.visit_date = request.visit_date
        m.visit_time = _visit_to_db(request.visit_time)
        m.zone_id = request.zone_id
        m.purpose = request.purpose
        m.status = _status_to_db(request.status)
        m.decision_by_id = request.decision_by_id
        m.decision_by_name = request.decision_by_name
        m.decision_comment = request.decision_comment
        m.reject_reason = (
            RejectReasonEnum(request.reject_reason.value) if request.reject_reason else None
        )
        m.clarification_question = request.clarification_question
        m.clarification_answer = request.clarification_answer
        m.updated_at = request.updated_at
        self._s.flush()

    def get(self, request_id: UUID) -> RequestEntity | None:
        m = self._s.get(RequestModel, request_id)
        if m is None:
            return None
        return self._to_entity(m)

    def list_by_initiator(self, initiator_user_id: UUID) -> list[RequestEntity]:
        rows = self._s.scalars(
            select(RequestModel)
            .where(RequestModel.initiator_user_id == initiator_user_id)
            .order_by(RequestModel.updated_at.desc())
        ).all()
        return [self._to_entity(r) for r in rows]

    def list_by_status(self, status: RequestStatus) -> list[RequestEntity]:
        rows = self._s.scalars(
            select(RequestModel)
            .where(RequestModel.status == _status_to_db(status))
            .order_by(RequestModel.updated_at.desc())
        ).all()
        return [self._to_entity(r) for r in rows]

    def allocate_number(self, year: int) -> str:
        seq = self._s.get(RequestNumberSeqModel, year)
        if seq is None:
            seq = RequestNumberSeqModel(year=year, last_value=100)
            self._s.add(seq)
        seq.last_value += 1
        self._s.flush()
        return f"GP-{year}-{seq.last_value:06d}"


class SqlAuditRepository(AuditRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def append(self, event: AuditEventEntity) -> None:
        self._s.add(
            AuditEventModel(
                id=event.id,
                request_id=event.request_id,
                event_type=event.event_type,
                actor_max_user_id=event.actor_max_user_id,
                actor_display_name=event.actor_display_name,
                payload=event.payload,
                created_at=event.created_at,
            )
        )

    def list_for_request(self, request_id: UUID) -> list[AuditEventEntity]:
        rows = self._s.scalars(
            select(AuditEventModel)
            .where(AuditEventModel.request_id == request_id)
            .order_by(AuditEventModel.created_at.desc())
        ).all()
        return [
            AuditEventEntity(
                id=r.id,
                request_id=r.request_id,
                event_type=r.event_type,
                actor_max_user_id=r.actor_max_user_id,
                actor_display_name=r.actor_display_name,
                payload=r.payload or {},
                created_at=r.created_at,
            )
            for r in rows
        ]


class SqlBotSessionRepository(BotSessionRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get(self, max_user_id: str) -> BotSessionEntity | None:
        m = self._s.get(BotSessionModel, max_user_id)
        if m is None:
            return None
        return BotSessionEntity(
            max_user_id=m.max_user_id,
            step=m.step,
            draft=m.draft or {},
            updated_at=m.updated_at,
        )

    def save(self, session: BotSessionEntity) -> None:
        m = self._s.get(BotSessionModel, session.max_user_id)
        if m is None:
            m = BotSessionModel(
                max_user_id=session.max_user_id,
                step=session.step,
                draft=session.draft,
            )
            self._s.add(m)
        else:
            m.step = session.step
            m.draft = session.draft
        self._s.flush()

    def delete(self, max_user_id: str) -> None:
        m = self._s.get(BotSessionModel, max_user_id)
        if m:
            self._s.delete(m)
