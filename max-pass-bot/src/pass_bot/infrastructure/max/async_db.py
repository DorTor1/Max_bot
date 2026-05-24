import asyncio
from collections.abc import Callable, Coroutine
from typing import TypeVar

from pass_bot.application.use_cases import Services
from pass_bot.infrastructure.config.settings import Settings
from pass_bot.infrastructure.container import services_scope

T = TypeVar("T")


async def run_db(settings: Settings, fn: Callable[[Services], T]) -> T:
    loop = asyncio.get_event_loop()

    def _inner() -> T:
        with services_scope(settings) as svc:
            return fn(svc)

    return await loop.run_in_executor(None, _inner)
