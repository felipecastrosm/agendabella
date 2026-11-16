"""Fixtures compartilhadas: banco SQLite em memória, dados fictícios e relógio fixo."""

from datetime import date, datetime, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import create_app
from app.models import Profissional, Servico
from app.routers import publico

# Segunda-feira, 23/11/2026, 08:00 — o "agora" de todos os testes.
AGORA = datetime(2026, 11, 23, 8, 0)
TERCA = date(2026, 11, 24)
DOMINGO = date(2026, 11, 29)


def relogio_fixo() -> datetime:
    return AGORA


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    try:
        yield sessao
    finally:
        sessao.close()
        engine.dispose()


@pytest.fixture
def dados(db):
    """Cria serviços e profissionais fictícios do Studio Bella Cabelos."""
    escova = Servico(nome="Escova", duracao_minutos=45, preco=50)
    corte = Servico(nome="Corte feminino", duracao_minutos=60, preco=70)
    inativo = Servico(nome="Serviço antigo", duracao_minutos=30, preco=10, ativo=False)
    ana = Profissional(
        nome="Ana",
        email="ana@studiobella.test",
        senha_hash="placeholder",
        papel="profissional",
        dias_atendimento="1,2,3,4,5",  # terça a sábado
        hora_inicio_expediente=time(9, 0),
        hora_fim_expediente=time(18, 0),
    )
    marcia = Profissional(
        nome="Márcia",
        email="marcia@studiobella.test",
        senha_hash="placeholder",
        papel="proprietaria",
        dias_atendimento="1,2,3,4,5",
        hora_inicio_expediente=time(9, 0),
        hora_fim_expediente=time(18, 0),
    )
    db.add_all([escova, corte, inativo, ana, marcia])
    db.commit()
    return {"escova": escova, "corte": corte, "inativo": inativo, "ana": ana, "marcia": marcia}


@pytest.fixture
def client(db):
    from app.services.agendamento_service import AgendamentoService

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[publico.get_agendamento_service] = lambda: AgendamentoService(
        db, relogio=relogio_fixo
    )
    return TestClient(app)
