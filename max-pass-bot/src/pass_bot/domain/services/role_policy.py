from pass_bot.domain.entities import UserEntity
from pass_bot.domain.enums import Role
from pass_bot.domain.exceptions import Forbidden


class RolePolicy:
    @staticmethod
    def require_initiator(user: UserEntity) -> None:
        if user.role != Role.INITIATOR or not user.is_active:
            raise Forbidden("Действие доступно только инициатору")

    @staticmethod
    def require_admin(user: UserEntity) -> None:
        if user.role not in (Role.ADMIN, Role.TECH_ADMIN) or not user.is_active:
            raise Forbidden("Нужна роль администратора ИБ")

    @staticmethod
    def require_tech_admin(user: UserEntity) -> None:
        if user.role != Role.TECH_ADMIN or not user.is_active:
            raise Forbidden("Нужна роль технического администратора")

    @staticmethod
    def can_view_request(user: UserEntity, *, initiator_max_id: str) -> bool:
        if user.role in (Role.ADMIN, Role.TECH_ADMIN):
            return True
        return user.max_user_id == initiator_max_id
