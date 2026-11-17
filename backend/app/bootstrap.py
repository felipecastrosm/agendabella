"""Carga inicial do salão (serviços e equipe) executada no início do container.

- Cria as tabelas, se não existirem.
- Insere serviços e profissionais apenas se o banco estiver vazio (idempotente).
- A senha inicial da equipe vem de BOOTSTRAP_SENHA; em produção ela é obrigatória
  e nunca fica no código-fonte. Sem ela, a equipe não é criada.
Uso: python -m app.bootstrap
"""

import logging
import os
from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Profissional, Servico
from app.security import gerar_hash

logger = logging.getLogger("agendabella.bootstrap")

SERVICOS = [
    ("Corte feminino", 60, 70.00),
    ("Escova", 45, 50.00),
    ("Coloração", 120, 150.00),
    ("Manicure", 45, 35.00),
]

PROFISSIONAIS = [
    ("Márcia", "marcia@studiobella.test", "proprietaria"),
    ("Ana", "ana@studiobella.test", "profissional"),
    ("Bruna", "bruna@studiobella.test", "profissional"),
    ("Carla", "carla@studiobella.test", "profissional"),
]


def popular(db: Session, senha: str | None) -> dict[str, int]:
    """Insere os dados iniciais se ainda não existirem. Retorna quantos registros criou."""
    criados = {"servicos": 0, "profissionais": 0}
    if db.scalar(select(Servico).limit(1)) is None:
        db.add_all(Servico(nome=n, duracao_minutos=d, preco=p) for n, d, p in SERVICOS)
        criados["servicos"] = len(SERVICOS)
    if db.scalar(select(Profissional).limit(1)) is None and senha:
        senha_hash = gerar_hash(senha)
        db.add_all(
            Profissional(
                nome=nome,
                email=email,
                senha_hash=senha_hash,
                papel=papel,
                dias_atendimento="1,2,3,4,5",  # terça a sábado
                hora_inicio_expediente=time(9, 0),
                hora_fim_expediente=time(18, 0),
            )
            for nome, email, papel in PROFISSIONAIS
        )
        criados["profissionais"] = len(PROFISSIONAIS)
    db.commit()
    return criados


def executar() -> None:
    logging.basicConfig(level=logging.INFO)
    senha = os.getenv("BOOTSTRAP_SENHA")
    if not senha and not settings.producao:
        senha = "senha-demo-123"  # apenas desenvolvimento local
    if not senha:
        logger.warning("BOOTSTRAP_SENHA não definida: a equipe não será criada.")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        criados = popular(db, senha)
    logger.info("Carga inicial concluída: %s", criados)


if __name__ == "__main__":
    executar()
