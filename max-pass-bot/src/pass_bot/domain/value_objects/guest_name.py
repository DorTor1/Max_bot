import re
from dataclasses import dataclass

from pass_bot.domain.exceptions import ValidationError

_NON_DIGIT = re.compile(r"[^\d\s]")


@dataclass(frozen=True)
class GuestName:
    value: str

    def __post_init__(self) -> None:
        v = self.value.strip()
        if len(v) < 2 or len(v) > 120:
            raise ValidationError("guest_full_name", "ФИО: от 2 до 120 символов")
        if not _NON_DIGIT.search(v):
            raise ValidationError(
                "guest_full_name",
                "ФИО не должно состоять только из цифр и пробелов",
            )
        object.__setattr__(self, "value", v)
