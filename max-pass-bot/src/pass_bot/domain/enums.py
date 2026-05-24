from enum import StrEnum


class Role(StrEnum):
    INITIATOR = "initiator"
    ADMIN = "admin"
    TECH_ADMIN = "tech_admin"


class RequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLARIFICATION = "clarification"
    CANCELLED = "cancelled"
    CLOSED = "closed"


class VisitTime(StrEnum):
    MORNING = "morning"
    DAY = "day"
    EVENING = "evening"


class RejectReason(StrEnum):
    INVALID_DATA = "INVALID_DATA"
    SECURITY_POLICY = "SECURITY_POLICY"
    DUPLICATE = "DUPLICATE"
    OTHER = "OTHER"


class AuditEventType(StrEnum):
    CREATED = "created"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLARIFICATION_REQUESTED = "clarification_requested"
    CLARIFICATION_ANSWERED = "clarification_answered"
    CANCELLED = "cancelled"
    CLOSED = "closed"
    CONSENT_ACCEPTED = "consent_accepted"


class WizardStep(StrEnum):
    CHOOSE_ZONE = "choose_zone"
    CHOOSE_TIME = "choose_time"
    CHOOSE_DATE = "choose_date"
    ENTER_GUEST_NAME = "enter_guest_name"
    ENTER_PURPOSE = "enter_purpose"
    CONFIRM = "confirm"
