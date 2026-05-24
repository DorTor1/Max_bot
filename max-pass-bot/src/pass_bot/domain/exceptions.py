from pass_bot.domain.enums import RequestStatus


class DomainError(Exception):
    """Базовая доменная ошибка."""


class ValidationError(DomainError):
    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(message)


class Forbidden(DomainError):
    def __init__(self, message: str = "Нет прав") -> None:
        super().__init__(message)


class NotFound(DomainError):
    def __init__(self, message: str = "Не найдено") -> None:
        super().__init__(message)


class Conflict(DomainError):
    def __init__(self, message: str = "Конфликт состояния") -> None:
        super().__init__(message)


class InvalidTransition(DomainError):
    def __init__(self, current: RequestStatus, target: RequestStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Переход {current.value} → {target.value} запрещён")
