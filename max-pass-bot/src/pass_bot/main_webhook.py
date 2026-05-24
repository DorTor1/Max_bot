import logging

import uvicorn

from pass_bot.bootstrap import create_app_stack, ensure_schema_and_seed
from pass_bot.interfaces.webhook.fastapi_webhook import build_webhook_app

logger = logging.getLogger(__name__)


async def _subscribe(bot, settings) -> None:
    if settings.webhook_public_url:
        try:
            await bot.subscribe_webhook(
                url=settings.webhook_public_url,
                secret=settings.webhook_secret,
            )
            logger.info("Webhook subscribed: %s", settings.webhook_public_url)
        except Exception as exc:
            logger.warning("subscribe_webhook failed: %s", exc)


def main() -> None:
    bot, dp, settings = create_app_stack()
    ensure_schema_and_seed(settings)
    app = build_webhook_app(
        dp,
        bot,
        secret=settings.webhook_secret,
        path=settings.webhook_path,
    )

    @app.on_event("startup")
    async def _on_startup_hook() -> None:
        await _subscribe(bot, settings)

    logger.info(
        "Webhook server %s:%s%s",
        settings.webhook_host,
        settings.webhook_port,
        settings.webhook_path,
    )
    uvicorn.run(
        app,
        host=settings.webhook_host,
        port=settings.webhook_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
