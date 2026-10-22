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
        
        for r in self.app.router.routes:
            print(type(r), vars(r))

    def remove_router(self, router: FastAPIRouterWrapper):
        api_router = router.api_router
        routes = self.app.router.routes

        def points_to_router(r) -> bool:
            # in fastapi 0.137+: router.routes is no longer a plain list of APIRoute objects, it can contain these intermediate objects that can contain additional routers, forming a tree.
            if r is api_router:
                return True
            return any(v is api_router for v in getattr(r, "__dict__", {}).values())

        routes[:] = [r for r in routes if not points_to_router(r)]


        # paths_to_check = frozenset(
        #     f"{router.api_router.prefix}{r.path}" for r in router.api_router.routes
        # )
        # for i, r in enumerate(self.app.router.routes):
        #     if r.path in paths_to_check:  # type: ignore
        #         del self.app.router.routes[i]

    def add_endpoint_method(
        self, coro: Callable[..., Coroutine], endpoint: str, method: str, **kwargs
    ):
        self.app.add_api_route(endpoint, coro, methods=[method], **kwargs)
