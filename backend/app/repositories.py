"""Repositórios: único ponto de acesso ao banco (padrão Repository).

Todas as consultas usam a API do SQLAlchemy, que gera SQL parametrizado,
evitando injeção de SQL (OWASP A03:2021).
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Agendamento, Cliente, Profissional, Servico, StatusAgendamento


class ServicoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_ativos(self) -> list[Servico]:
        return list(self.db.scalars(select(Servico).where(Servico.ativo).order_by(Servico.nome)))

    def obter_ativo(self, id_servico: int) -> Servico | None:
        return self.db.scalar(select(Servico).where(Servico.id == id_servico, Servico.ativo))


class ProfissionalRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_ativas(self) -> list[Profissional]:
        return list(
            self.db.scalars(
                select(Profissional).where(Profissional.ativo).order_by(Profissional.nome)
            )
        )

    def obter_ativa(self, id_profissional: int) -> Profissional | None:
        return self.db.scalar(
            select(Profissional).where(Profissional.id == id_profissional, Profissional.ativo)
        )

    def obter_por_email(self, email: str) -> Profissional | None:
        return self.db.scalar(select(Profissional).where(Profissional.email == email.lower()))


class ClienteRepository:
    def __init__(self, db: Session):
        self.db = db

    def obter_por_telefone(self, telefone: str) -> Cliente | None:
        return self.db.scalar(select(Cliente).where(Cliente.telefone == telefone))

    def obter_ou_criar(self, nome: str, telefone: str) -> Cliente:
        cliente = self.obter_por_telefone(telefone)
        if cliente is None:
            cliente = Cliente(nome=nome, telefone=telefone)
            self.db.add(cliente)
            self.db.flush()
        return cliente


class AgendamentoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_ativos_do_dia(self, id_profissional: int, dia: date) -> list[Agendamento]:
        return list(
            self.db.scalars(
                select(Agendamento)
                .where(
                    Agendamento.id_profissional == id_profissional,
                    Agendamento.data == dia,
                    Agendamento.status != StatusAgendamento.CANCELADO.value,
                )
                .order_by(Agendamento.hora_inicio)
            )
        )

    def listar_periodo(self, inicio: date, fim: date) -> list[Agendamento]:
        return list(
            self.db.scalars(
                select(Agendamento)
                .options(
                    joinedload(Agendamento.cliente),
                    joinedload(Agendamento.profissional),
                    joinedload(Agendamento.servico),
                )
                .where(Agendamento.data >= inicio, Agendamento.data <= fim)
                .order_by(Agendamento.data, Agendamento.hora_inicio)
            )
        )

    def obter(self, id_agendamento: int) -> Agendamento | None:
        return self.db.get(Agendamento, id_agendamento)

    def adicionar(self, agendamento: Agendamento) -> Agendamento:
        self.db.add(agendamento)
        self.db.flush()
        return agendamento
