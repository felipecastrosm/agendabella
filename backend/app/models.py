"""Entidades do domínio: Profissional, Cliente, Servico e Agendamento."""

from datetime import date, datetime, time
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Time,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Papel(str, Enum):
    PROPRIETARIA = "proprietaria"
    PROFISSIONAL = "profissional"


class StatusAgendamento(str, Enum):
    CONFIRMADO = "confirmado"
    REALIZADO = "realizado"
    FALTA = "falta"
    CANCELADO = "cancelado"


class Profissional(Base):
    __tablename__ = "profissional"
    __table_args__ = (
        CheckConstraint("hora_fim_expediente > hora_inicio_expediente", name="ck_expediente"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    papel: Mapped[str] = mapped_column(String(20), default=Papel.PROFISSIONAL.value)
    # dias da semana em que atende: 0=segunda ... 6=domingo, separados por vírgula
    dias_atendimento: Mapped[str] = mapped_column(String(20), default="1,2,3,4,5")
    hora_inicio_expediente: Mapped[time] = mapped_column(Time)
    hora_fim_expediente: Mapped[time] = mapped_column(Time)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    agendamentos: Mapped[list["Agendamento"]] = relationship(back_populates="profissional")

    def atende_no_dia(self, dia: date) -> bool:
        dias = {int(d) for d in self.dias_atendimento.split(",") if d.strip()}
        return dia.weekday() in dias


class Cliente(Base):
    __tablename__ = "cliente"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    telefone: Mapped[str] = mapped_column(String(11), unique=True)
    data_cadastro: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    agendamentos: Mapped[list["Agendamento"]] = relationship(back_populates="cliente")


class Servico(Base):
    __tablename__ = "servico"
    __table_args__ = (
        CheckConstraint("duracao_minutos > 0 AND duracao_minutos % 15 = 0", name="ck_duracao"),
        CheckConstraint("preco >= 0", name="ck_preco"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True)
    duracao_minutos: Mapped[int] = mapped_column(Integer)
    preco: Mapped[float] = mapped_column(Numeric(8, 2))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    agendamentos: Mapped[list["Agendamento"]] = relationship(back_populates="servico")


class Agendamento(Base):
    __tablename__ = "agendamento"
    __table_args__ = (
        # Impede, no próprio banco, dois agendamentos ativos no mesmo início para a mesma profissional.
        Index(
            "uq_agendamento_ativo",
            "id_profissional",
            "data",
            "hora_inicio",
            unique=True,
            sqlite_where=text("status <> 'cancelado'"),
            postgresql_where=text("status <> 'cancelado'"),
        ),
        Index("ix_agendamento_profissional_data", "id_profissional", "data"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("cliente.id"))
    id_profissional: Mapped[int] = mapped_column(ForeignKey("profissional.id"))
    id_servico: Mapped[int] = mapped_column(ForeignKey("servico.id"))
    data: Mapped[date] = mapped_column(Date)
    hora_inicio: Mapped[time] = mapped_column(Time)
    hora_fim: Mapped[time] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(20), default=StatusAgendamento.CONFIRMADO.value)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    cliente: Mapped[Cliente] = relationship(back_populates="agendamentos")
    profissional: Mapped[Profissional] = relationship(back_populates="agendamentos")
    servico: Mapped[Servico] = relationship(back_populates="agendamentos")
