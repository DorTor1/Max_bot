import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RoleEnum(str, enum.Enum):
    initiator = "initiator"
    admin = "admin"
    tech_admin = "tech_admin"


class RequestStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    clarification = "clarification"
    cancelled = "cancelled"
    closed = "closed"


class VisitTimeEnum(str, enum.Enum):
    morning = "morning"
    day = "day"
    evening = "evening"


class RejectReasonEnum(str, enum.Enum):
    INVALID_DATA = "INVALID_DATA"
    SECURITY_POLICY = "SECURITY_POLICY"
    DUPLICATE = "DUPLICATE"
    OTHER = "OTHER"


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    max_user_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.initiator)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    consents: Mapped[list["ConsentRecordModel"]] = relationship(back_populates="user")
    requests: Mapped[list["RequestModel"]] = relationship(back_populates="initiator")


class ConsentRecordModel(Base):
    __tablename__ = "consent_records"
    __table_args__ = (UniqueConstraint("user_id", "doc_version"),)

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    doc_version: Mapped[str] = mapped_column(String(32), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    ip_meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped[UserModel] = relationship(back_populates="consents")


class ZoneModel(Base):
    __tablename__ = "zones"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class RequestModel(Base):
    __tablename__ = "requests"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    guest_full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)
    visit_time: Mapped[VisitTimeEnum] = mapped_column(Enum(VisitTimeEnum), nullable=False)
    zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RequestStatusEnum] = mapped_column(
        Enum(RequestStatusEnum), default=RequestStatusEnum.pending
    )
    initiator_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    decision_by_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision_by_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    decision_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reject_reason: Mapped[RejectReasonEnum | None] = mapped_column(Enum(RejectReasonEnum), nullable=True)
    clarification_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    clarification_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    initiator: Mapped[UserModel] = relationship(back_populates="requests")
    zone: Mapped[ZoneModel] = relationship()
    audit_events: Mapped[list["AuditEventModel"]] = relationship(back_populates="request")


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("requests.id"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_max_user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    request: Mapped[RequestModel | None] = relationship(back_populates="audit_events")


class BotSessionModel(Base):
    __tablename__ = "bot_sessions"

    max_user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    step: Mapped[str] = mapped_column(String(64), nullable=False)
    draft: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RequestNumberSeqModel(Base):
    __tablename__ = "request_number_seq"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_value: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
