import logging

from maxapi import Bot, Dispatcher

from pass_bot.infrastructure.config.settings import Settings, get_settings
from pass_bot.infrastructure.max.handlers import register_handlers
from pass_bot.infrastructure.persistence.db import init_db
from pass_bot.infrastructure.persistence.models import Base
from pass_bot.infrastructure.persistence.seed import seed_database
from pass_bot.infrastructure.persistence.db import get_engine, session_scope


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def create_app_stack(settings: Settings | None = None) -> tuple[Bot, Dispatcher, Settings]:
    settings = settings or get_settings()
    setup_logging(settings.log_level)
    init_db(settings)
    bot = Bot(settings.bot_token)
    dp = Dispatcher()
    register_handlers(dp, bot, settings)
    return bot, dp, settings


def ensure_schema_and_seed(settings: Settings) -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)
    with session_scope() as session:
        seed_database(session, settings)
