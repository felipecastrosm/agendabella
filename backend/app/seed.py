"""Popula o banco local com dados FICTÍCIOS para demonstração.

Uso: python -m app.seed
As senhas de demonstração vêm de SEED_SENHA (padrão apenas para ambiente local).
"""

import os
from datetime import time

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Profissional, Servico
from app.security import gerar_hash

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


def executar() -> None:
    if os.getenv("APP_ENV") == "production":
        raise SystemExit("O seed de demonstração não deve ser executado em produção.")
    senha = os.getenv("SEED_SENHA", "senha-demo-123")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(Servico).limit(1)) is not None:
            print("Banco já populado; nada a fazer.")
            return
        db.add_all(Servico(nome=n, duracao_minutos=d, preco=p) for n, d, p in SERVICOS)
        hash_demo = gerar_hash(senha)
        db.add_all(
            Profissional(
                nome=nome,
                email=email,
                senha_hash=hash_demo,
                papel=papel,
                dias_atendimento="1,2,3,4,5",  # terça a sábado
                hora_inicio_expediente=time(9, 0),
                hora_fim_expediente=time(18, 0),
            )
            for nome, email, papel in PROFISSIONAIS
        )
        db.commit()
    print("Banco populado com dados fictícios.")


if __name__ == "__main__":
    executar()
