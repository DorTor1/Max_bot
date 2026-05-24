"""FastAPI-интеграция webhook MAX (аналог maxapi.webhook.aiohttp)."""

from __future__ import annotations

from http import HTTPStatus
from secrets import compare_digest
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, Request, Response
from maxapi.webhook.base import BaseMaxWebhook

if TYPE_CHECKING:
    from maxapi import Bot
    from maxapi.dispatcher import Dispatcher


class FastApiMaxWebhook(BaseMaxWebhook):
    def create_app(self, path: str = "/max/webhook") -> FastAPI:
        app = FastAPI(title="MAX Pass Bot")

        @app.on_event("startup")
        async def _startup() -> None:
            await self._startup()

        @app.get("/health")
        async def health() -> dict[str, str]:
            return {"status": "ok"}

        secret = self.secret

        @app.post(path)
        async def webhook_handler(request: Request) -> Response:
            if secret is not None:
                incoming = request.headers.get("X-Max-Bot-Api-Secret")
                if incoming is None or not compare_digest(incoming, secret):
                    return Response(status_code=HTTPStatus.FORBIDDEN, content="Forbidden")
            event_json: dict[str, Any] = await request.json()
            await self._dispatch(event_json)
            return Response(status_code=HTTPStatus.OK, content='{"ok":true}')

        return app


def build_webhook_app(
    dp: "Dispatcher", bot: "Bot", *, secret: str | None, path: str
) -> FastAPI:
    hook = FastApiMaxWebhook(dp=dp, bot=bot, secret=secret)
    return hook.create_app(path=path)
