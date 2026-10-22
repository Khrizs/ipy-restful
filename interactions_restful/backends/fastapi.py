from contextlib import asynccontextmanager
from typing import Callable, Coroutine

from fastapi import APIRouter, FastAPI
from interactions import Client

from ..abc import BaseAPIHandler, BaseRouterWrapper

__all__ = ("FastAPIHandler",)


class FastAPIRouterWrapper(BaseRouterWrapper):
    def __init__(self, **kwargs):
        kwargs.pop("name")  # neccessary only for quart
        self.api_router = APIRouter(**kwargs)

    def add_endpoint_method(
        self, coro: Callable[..., Coroutine], endpoint: str, method: str, **kwargs
    ):
        self.api_router.add_api_route(endpoint, coro, methods=[method], **kwargs)


class FastAPIHandler(BaseAPIHandler):
    app: FastAPI

    def __init__(self, bot: Client, app: FastAPI):
        super().__init__(bot, app)
        existing_lifespan = self.app.router.lifespan_context

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            async with existing_lifespan(app):
                await self.startup()
                yield
                await self.shutdown()

        self.app.router.lifespan_context = lifespan

    @staticmethod
    def create_router(**kwargs):
        return FastAPIRouterWrapper(**kwargs)

    def add_router(self, router: FastAPIRouterWrapper):
        self.app.include_router(router.api_router)

    def remove_router(self, router: FastAPIRouterWrapper):
        # in fastapi 0.137+: router.routes is no longer a plain list of APIRoute objects, it can contain these intermediate objects that can contain additional routers, forming a tree.
        routes = self.app.router.routes
        routes[:] = [r for r in routes if getattr(r, "original_router", None) is not router.api_router]

    def add_endpoint_method(
        self, coro: Callable[..., Coroutine], endpoint: str, method: str, **kwargs
    ):
        self.app.add_api_route(endpoint, coro, methods=[method], **kwargs)
