from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID, uuid4

from pass_bot.domain.enums import (
    RejectReason,
    RequestStatus,
    Role,
    VisitTime,
)


@dataclass
class UserEntity:
    id: UUID
    max_user_id: str
    display_name: str
    role: Role
    is_active: bool = True


@dataclass
class ZoneEntity:
    id: str
    title: str
    sort_order: int = 0


@dataclass
class RequestEntity:
    id: UUID
    number: str
    guest_full_name: str
    visit_date: date
    visit_time: VisitTime
    zone_id: str
    zone_title: str
    purpose: str
    status: RequestStatus
    initiator_user_id: UUID
    initiator_max_id: str
    initiator_display_name: str
    created_at: datetime
    updated_at: datetime
    decision_by_id: str | None = None
    decision_by_name: str | None = None
    decision_comment: str | None = None
    reject_reason: RejectReason | None = None
    clarification_question: str | None = None
    clarification_answer: str | None = None

    @classmethod
    def create_pending(
        cls,
        *,
        number: str,
        guest_full_name: str,
        visit_date: date,
        visit_time: VisitTime,
        zone: ZoneEntity,
        purpose: str,
        initiator: UserEntity,
        now: datetime,
    ) -> "RequestEntity":
        rid = uuid4()
        return cls(
            id=rid,
            number=number,
            guest_full_name=guest_full_name,
            visit_date=visit_date,
            visit_time=visit_time,
            zone_id=zone.id,
            zone_title=zone.title,
            purpose=purpose,
            status=RequestStatus.PENDING,
            initiator_user_id=initiator.id,
            initiator_max_id=initiator.max_user_id,
            initiator_display_name=initiator.display_name,
            created_at=now,
            updated_at=now,
        )


@dataclass
class BotSessionEntity:
    max_user_id: str
    step: str
    draft: dict = field(default_factory=dict)
    updated_at: datetime | None = None


@dataclass
class AuditEventEntity:
    id: UUID
    request_id: UUID | None
    event_type: str
    actor_max_user_id: str
    actor_display_name: str
    payload: dict
    created_at: datetime
