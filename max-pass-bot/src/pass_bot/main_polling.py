import asyncio
import logging

from pass_bot.bootstrap import create_app_stack, ensure_schema_and_seed

logger = logging.getLogger(__name__)


async def _run() -> None:
    bot, dp, settings = create_app_stack()
    ensure_schema_and_seed(settings)
    logger.info("Starting long polling…")
    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
