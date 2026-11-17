"""Popula o banco LOCAL com dados fictícios para demonstração.

Uso: python -m app.seed  (bloqueado em produção; lá a carga é feita por app.bootstrap)
"""

import os

from app.bootstrap import executar as executar_bootstrap


def executar() -> None:
    if os.getenv("APP_ENV") == "production":
        raise SystemExit("O seed de demonstração não deve ser executado em produção.")
    executar_bootstrap()


if __name__ == "__main__":
    executar()
