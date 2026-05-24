from dataclasses import dataclass
from datetime import date

from pass_bot.domain.exceptions import ValidationError


@dataclass(frozen=True)
class VisitDate:
    value: date

    @classmethod
    def from_iso(cls, raw: str, *, today: date) -> "VisitDate":
        try:
            d = date.fromisoformat(raw)
        except ValueError as exc:
            raise ValidationError("visit_date", "Некорректная дата") from exc
        if d < today:
            raise ValidationError("visit_date", "Дата не может быть в прошлом")
        return cls(d)
