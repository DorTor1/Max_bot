from pass_bot.domain.enums import RequestStatus, Role
from pass_bot.domain.exceptions import InvalidTransition


class RequestStateMachine:
    def ensure_transition(
        self,
        current: RequestStatus,
        target: RequestStatus,
        *,
        role: Role,
        is_initiator: bool,
    ) -> None:
        allowed: dict[tuple[RequestStatus, RequestStatus], bool] = {
            (RequestStatus.PENDING, RequestStatus.APPROVED): role
            in (Role.ADMIN, Role.TECH_ADMIN),
            (RequestStatus.PENDING, RequestStatus.REJECTED): role
            in (Role.ADMIN, Role.TECH_ADMIN),
            (RequestStatus.PENDING, RequestStatus.CLARIFICATION): role
            in (Role.ADMIN, Role.TECH_ADMIN),
            (RequestStatus.PENDING, RequestStatus.CANCELLED): is_initiator,
            (RequestStatus.CLARIFICATION, RequestStatus.PENDING): is_initiator,
            (RequestStatus.CLARIFICATION, RequestStatus.CANCELLED): is_initiator,
            (RequestStatus.APPROVED, RequestStatus.CLOSED): role
            in (Role.ADMIN, Role.TECH_ADMIN),
            (RequestStatus.REJECTED, RequestStatus.CLOSED): role
            in (Role.ADMIN, Role.TECH_ADMIN),
        }
        if allowed.get((current, target)) is not True:
            raise InvalidTransition(current, target)
