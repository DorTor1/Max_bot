from sqlalchemy import select
from sqlalchemy.orm import Session

from pass_bot.domain.enums import Role
from pass_bot.infrastructure.config.settings import Settings
from pass_bot.infrastructure.persistence.models import RoleEnum, UserModel, ZoneModel

ZONES = [
    ("main", "Главный корпус", 0),
    ("lab-a", "Лабораторный корпус A", 1),
    ("dorm-3", "Общежитие №3", 2),
    ("library", "Наука — библиотека", 3),
]


def seed_database(session: Session, settings: Settings) -> None:
    for zid, title, order in ZONES:
        if session.get(ZoneModel, zid) is None:
            session.add(ZoneModel(id=zid, title=title, sort_order=order))

    for max_id in settings.tech_admin_ids():
        user = session.scalar(select(UserModel).where(UserModel.max_user_id == max_id))
        if user is None:
            session.add(
                UserModel(
                    max_user_id=max_id,
                    display_name=f"Tech Admin {max_id}",
                    role=RoleEnum.tech_admin,
                )
            )
        else:
            user.role = RoleEnum.tech_admin

    session.flush()
