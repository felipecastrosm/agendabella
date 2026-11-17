"""Ponto de entrada da API AgendaBella."""

import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.routers import auth, painel, publico

logger = logging.getLogger("agendabella")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


_PADRAO = object()


def create_app(frontend_dist: Path | None | object = _PADRAO) -> FastAPI:
    """Cria a aplicação. `frontend_dist=None` desliga a entrega do front-end (útil em testes)."""
    if frontend_dist is _PADRAO:
        frontend_dist = Path(settings.frontend_dist)
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

    @app.middleware("http")
    async def cabecalhos_de_seguranca(request: Request, call_next):
        # Endurecimento de respostas HTTP (OWASP A05:2021, configuração segura).
        resposta = await call_next(request)
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        resposta.headers["X-Frame-Options"] = "DENY"
        resposta.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path.startswith("/api/"):
            resposta.headers["Cache-Control"] = "no-store"
        if settings.producao:
            resposta.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return resposta

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
    def saude(db: Session = Depends(get_db)):
        """Verificação de saúde usada pelo Render e pelo monitoramento: inclui o banco."""
        try:
            db.execute(text("SELECT 1"))
        except Exception:
            logger.exception("Falha na verificação de saúde do banco")
            return JSONResponse(status_code=503, content={"status": "indisponivel"})
        return {"status": "ok"}

    app.include_router(publico.router)
    app.include_router(auth.router)
    app.include_router(painel.router)
    if frontend_dist is not None:
        montar_frontend(app, frontend_dist)
    return app


def montar_frontend(app: FastAPI, pasta: Path) -> None:
    """Serve o build do Angular na mesma origem da API (SPA com fallback para index.html)."""
    if not (pasta / "index.html").is_file():
        return
    raiz = pasta.resolve()

    @app.api_route("/{caminho:path}", methods=["GET", "HEAD"], include_in_schema=False)
    def frontend(caminho: str):
        if caminho.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Recurso não encontrado."})
        arquivo = (raiz / caminho).resolve()
        # Impede path traversal: só entrega arquivos dentro da pasta do build.
        if caminho and arquivo.is_file() and arquivo.is_relative_to(raiz):
            cache = "public, max-age=31536000, immutable" if _tem_hash(arquivo.name) else "no-cache"
            return FileResponse(arquivo, headers={"Cache-Control": cache})
        return FileResponse(raiz / "index.html", headers={"Cache-Control": "no-cache"})


def _tem_hash(nome: str) -> bool:
    # Arquivos gerados pelo build do Angular têm hash no nome (ex.: main-ZSQLK7KA.js).
    base = nome.rsplit(".", 1)[0]
    return "-" in base and base.rsplit("-", 1)[1].isalnum() and len(base.rsplit("-", 1)[1]) >= 8


app = create_app()
