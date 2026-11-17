"""Configurações lidas de variáveis de ambiente (nenhum segredo no código)."""

import os
from dataclasses import dataclass, field


def _lista(valor: str) -> list[str]:
    return [item.strip() for item in valor.split(",") if item.strip()]


def normalizar_database_url(url: str) -> str:
    """Provedores como o Render entregam "postgres://"; o SQLAlchemy 2 + psycopg 3
    espera "postgresql+psycopg://"."""
    for prefixo in ("postgres://", "postgresql://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url[len(prefixo):]
    return url


@dataclass(frozen=True)
class Settings:
    database_url: str = field(
        default_factory=lambda: normalizar_database_url(
            os.getenv("DATABASE_URL", "sqlite:///./agendabella.db")
        )
    )
    # Pasta com o build de produção do Angular; quando existe, a API também serve o front-end.
    frontend_dist: str = field(
        default_factory=lambda: os.getenv("FRONTEND_DIST", "../frontend/dist/frontend/browser")
    )
    jwt_secret: str = field(
        default_factory=lambda: os.getenv("JWT_SECRET", "dev-secret-troque-em-producao")
    )
    jwt_algoritmo: str = "HS256"
    jwt_expiracao_horas: int = 8
    cors_origins: list[str] = field(
        default_factory=lambda: _lista(os.getenv("CORS_ORIGINS", "http://localhost:4200"))
    )
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    max_falhas_login: int = 5
    janela_bloqueio_minutos: int = 15

    @property
    def producao(self) -> bool:
        return self.app_env == "production"


settings = Settings()
