from datetime import date

import pytest

from pass_bot.domain.enums import RequestStatus, Role
from pass_bot.domain.exceptions import InvalidTransition, ValidationError
from pass_bot.domain.services.request_state_machine import RequestStateMachine
from pass_bot.domain.value_objects import GuestName, Purpose, VisitDate


def test_guest_name_rejects_digits_only() -> None:
    with pytest.raises(ValidationError):
        GuestName("12345")


def test_guest_name_accepts_valid() -> None:
    assert GuestName("Иван Петров").value == "Иван Петров"


def test_visit_date_not_in_past() -> None:
    with pytest.raises(ValidationError):
        VisitDate.from_iso("2020-01-01", today=date(2026, 5, 24))


def test_purpose_min_length() -> None:
    with pytest.raises(ValidationError):
        Purpose("ab")


def test_state_machine_initiator_cancel() -> None:
    sm = RequestStateMachine()
    sm.ensure_transition(
        RequestStatus.PENDING,
        RequestStatus.CANCELLED,
        role=Role.INITIATOR,
        is_initiator=True,
    )


def test_state_machine_admin_cannot_cancel() -> None:
    sm = RequestStateMachine()
    with pytest.raises(InvalidTransition):
        sm.ensure_transition(
            RequestStatus.PENDING,
            RequestStatus.CANCELLED,
            role=Role.ADMIN,
            is_initiator=False,
        )
