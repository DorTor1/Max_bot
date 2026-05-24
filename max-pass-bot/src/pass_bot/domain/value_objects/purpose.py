from dataclasses import dataclass

from pass_bot.domain.exceptions import ValidationError


@dataclass(frozen=True)
class Purpose:
    value: str

    def __post_init__(self) -> None:
        v = self.value.strip()
        if len(v) < 3 or len(v) > 500:
            raise ValidationError("purpose", "Цель визита: от 3 до 500 символов")
        object.__setattr__(self, "value", v)
