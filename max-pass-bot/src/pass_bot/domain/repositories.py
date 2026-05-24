from abc import ABC, abstractmethod
from datetime import date, datetime
from uuid import UUID

from pass_bot.domain.entities import (
    AuditEventEntity,
    BotSessionEntity,
    RequestEntity,
    UserEntity,
    ZoneEntity,
)
from pass_bot.domain.enums import AuditEventType, RequestStatus, Role


class ClockPort(ABC):
    @abstractmethod
    def now(self) -> datetime: ...

    @abstractmethod
    def today(self) -> date: ...


class UserRepository(ABC):
    @abstractmethod
    def get_by_max_id(self, max_user_id: str) -> UserEntity | None: ...

    @abstractmethod
    def upsert_from_max(
        self, max_user_id: str, display_name: str, *, default_role: Role
    ) -> UserEntity: ...

    @abstractmethod
    def set_role(self, max_user_id: str, role: Role) -> UserEntity: ...

    @abstractmethod
    def list_by_role(self, role: Role) -> list[UserEntity]: ...


class ConsentRepository(ABC):
    @abstractmethod
    def has_consent(self, user_id: UUID, doc_version: str) -> bool: ...

    @abstractmethod
    def record(
        self,
        user: UserEntity,
        doc_version: str,
        *,
        accepted_at: datetime,
    ) -> None: ...


class ZoneRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[ZoneEntity]: ...

    @abstractmethod
    def get(self, zone_id: str) -> ZoneEntity | None: ...


class RequestRepository(ABC):
    @abstractmethod
    def save(self, request: RequestEntity) -> None: ...

    @abstractmethod
    def get(self, request_id: UUID) -> RequestEntity | None: ...

    @abstractmethod
    def list_by_initiator(self, initiator_user_id: UUID) -> list[RequestEntity]: ...

    @abstractmethod
    def list_by_status(self, status: RequestStatus) -> list[RequestEntity]: ...

    @abstractmethod
    def allocate_number(self, year: int) -> str: ...


class AuditRepository(ABC):
    @abstractmethod
    def append(self, event: AuditEventEntity) -> None: ...

    @abstractmethod
    def list_for_request(self, request_id: UUID) -> list[AuditEventEntity]: ...


class BotSessionRepository(ABC):
    @abstractmethod
    def get(self, max_user_id: str) -> BotSessionEntity | None: ...

    @abstractmethod
    def save(self, session: BotSessionEntity) -> None: ...

    @abstractmethod
    def delete(self, max_user_id: str) -> None: ...


def audit_event(
    *,
    request_id: UUID | None,
    event_type: AuditEventType,
    actor: UserEntity,
    payload: dict | None = None,
    now: datetime,
) -> AuditEventEntity:
    from uuid import uuid4

    return AuditEventEntity(
        id=uuid4(),
        request_id=request_id,
        event_type=event_type.value,
        actor_max_user_id=actor.max_user_id,
        actor_display_name=actor.display_name,
        payload=payload or {},
        created_at=now,
    )
