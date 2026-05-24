from collections.abc import Callable
from contextlib import contextmanager
from typing import Generator

from pass_bot.application.use_cases import Services
from pass_bot.infrastructure.config.settings import Settings
from pass_bot.infrastructure.persistence.db import session_scope
from pass_bot.infrastructure.persistence.repositories import (
    SqlAuditRepository,
    SqlBotSessionRepository,
    SqlConsentRepository,
    SqlRequestRepository,
    SqlUserRepository,
    SqlZoneRepository,
    SystemClock,
)


@contextmanager
def services_scope(settings: Settings) -> Generator[Services]:
    with session_scope() as session:
        clock = SystemClock()
        yield Services(
            users=SqlUserRepository(session, settings.tech_admin_ids()),
            consent=SqlConsentRepository(session),
            zones=SqlZoneRepository(session),
            requests=SqlRequestRepository(session),
            audit=SqlAuditRepository(session),
            sessions=SqlBotSessionRepository(session),
            clock=clock,
            consent_version=settings.consent_version,
        )


def run_with_services(
    settings: Settings, fn: Callable[[Services], None]
) -> None:
    with services_scope(settings) as svc:
        fn(svc)
