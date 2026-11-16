"""Ponto de entrada da API AgendaBella."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine
from app.routers import auth, painel, publico

logger = logging.getLogger("agendabella")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="AgendaBella API",
        version="1.0.0",
        lifespan=lifespan,
        # Documentação interativa desabilitada em produção (OWASP A05:2021).
        docs_url=None if settings.producao else "/docs",
        redoc_url=None,
        openapi_url=None if settings.producao else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.exception_handler(RequestValidationError)
    async def erro_validacao(_: Request, exc: RequestValidationError):
        # Devolve apenas as mensagens de validação, sem detalhes internos.
        mensagens = [str(e.get("msg", "Dado inválido")).removeprefix("Value error, ") for e in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": mensagens})

    @app.exception_handler(Exception)
    async def erro_inesperado(_: Request, exc: Exception):
        logger.exception("Erro inesperado: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Ocorreu um erro inesperado. Tente novamente em instantes."},
        )

    @app.get("/api/saude", tags=["infra"])
    def saude():
        return {"status": "ok"}

    app.include_router(publico.router)
    app.include_router(auth.router)
    app.include_router(painel.router)
    return app


app = create_app()
