"""Regras de negócio do agendamento (RF01, RF02 e RF05).

Esta camada concentra a regra mais crítica do MVP: calcular horários livres
e impedir que dois agendamentos não cancelados da mesma profissional se
sobreponham, total ou parcialmente.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Agendamento, Profissional, Servico, StatusAgendamento
from app.repositories import (
    AgendamentoRepository,
    ClienteRepository,
    ProfissionalRepository,
    ServicoRepository,
)

PASSO_MINUTOS = 15
ANTECEDENCIA_MINIMA_MINUTOS = 30


class RegraNegocioError(Exception):
    """Erro de regra de negócio com mensagem segura para exibir ao usuário."""


class RecursoNaoEncontrado(RegraNegocioError):
    pass


class ConflitoHorario(RegraNegocioError):
    def __init__(self, alternativas: list[str]):
        super().__init__("Este horário acabou de ser reservado. Escolha outro horário disponível.")
        self.alternativas = alternativas


@dataclass(frozen=True)
class Intervalo:
    inicio: time
    fim: time

    def sobrepoe(self, outro: "Intervalo") -> bool:
        return self.inicio < outro.fim and outro.inicio < self.fim


def somar_minutos(hora: time, minutos: int) -> time:
    return (datetime.combine(date.min, hora) + timedelta(minutes=minutos)).time()


def calcular_horarios_livres(
    profissional: Profissional,
    servico: Servico,
    dia: date,
    ocupados: list[Intervalo],
    agora: datetime,
) -> list[time]:
    """Função pura: gera os inícios possíveis respeitando expediente, duração e ocupação."""
    if not profissional.atende_no_dia(dia):
        return []

    limite = agora + timedelta(minutes=ANTECEDENCIA_MINIMA_MINUTOS)
    livres: list[time] = []
    inicio = profissional.hora_inicio_expediente
    while True:
        fim = somar_minutos(inicio, servico.duracao_minutos)
        if fim > profissional.hora_fim_expediente or fim <= inicio:
            break
        candidato = Intervalo(inicio, fim)
        no_futuro = datetime.combine(dia, inicio) >= limite
        if no_futuro and not any(candidato.sobrepoe(o) for o in ocupados):
            livres.append(inicio)
        inicio = somar_minutos(inicio, PASSO_MINUTOS)
        if inicio <= profissional.hora_inicio_expediente:  # proteção contra virada do dia
            break
    return livres


class AgendamentoService:
    def __init__(self, db: Session, relogio: Callable[[], datetime] = datetime.now):
        self.db = db
        self.relogio = relogio
        self.servicos = ServicoRepository(db)
        self.profissionais = ProfissionalRepository(db)
        self.clientes = ClienteRepository(db)
        self.agendamentos = AgendamentoRepository(db)

    def _carregar(self, id_servico: int, id_profissional: int) -> tuple[Servico, Profissional]:
        servico = self.servicos.obter_ativo(id_servico)
        profissional = self.profissionais.obter_ativa(id_profissional)
        if servico is None or profissional is None:
            raise RecursoNaoEncontrado("Serviço ou profissional indisponível.")
        return servico, profissional

    def _ocupados(self, id_profissional: int, dia: date) -> list[Intervalo]:
        return [
            Intervalo(a.hora_inicio, a.hora_fim)
            for a in self.agendamentos.listar_ativos_do_dia(id_profissional, dia)
        ]

    def horarios_disponiveis(self, id_servico: int, id_profissional: int, dia: date) -> list[time]:
        """RF01: lista os horários livres para o serviço, a profissional e a data."""
        servico, profissional = self._carregar(id_servico, id_profissional)
        return calcular_horarios_livres(
            profissional, servico, dia, self._ocupados(id_profissional, dia), self.relogio()
        )

    def agendar(
        self,
        id_servico: int,
        id_profissional: int,
        dia: date,
        hora_inicio: time,
        nome: str,
        telefone: str,
    ) -> Agendamento:
        """RF02: grava o agendamento refazendo a verificação de conflito no momento da gravação."""
        servico, profissional = self._carregar(id_servico, id_profissional)
        livres = calcular_horarios_livres(
            profissional, servico, dia, self._ocupados(id_profissional, dia), self.relogio()
        )
        if hora_inicio not in livres:
            raise ConflitoHorario([h.strftime("%H:%M") for h in livres[:6]])

        cliente = self.clientes.obter_ou_criar(nome, telefone)
        agendamento = Agendamento(
            id_cliente=cliente.id,
            id_profissional=profissional.id,
            id_servico=servico.id,
            data=dia,
            hora_inicio=hora_inicio,
            hora_fim=somar_minutos(hora_inicio, servico.duracao_minutos),
            status=StatusAgendamento.CONFIRMADO.value,
        )
        try:
            self.agendamentos.adicionar(agendamento)
            self.db.commit()
        except IntegrityError:
            # Corrida entre duas gravações simultâneas: o índice único do banco barra a segunda.
            self.db.rollback()
            restantes = self.horarios_disponiveis(id_servico, id_profissional, dia)
            raise ConflitoHorario([h.strftime("%H:%M") for h in restantes[:6]]) from None
        self.db.refresh(agendamento)
        return agendamento

    def alterar_status(self, id_agendamento: int, novo_status: str) -> Agendamento:
        """RF05: atualiza o status; realizado/falta só são permitidos após o início do horário."""
        agendamento = self.agendamentos.obter(id_agendamento)
        if agendamento is None:
            raise RecursoNaoEncontrado("Agendamento não encontrado.")
        if novo_status in (StatusAgendamento.REALIZADO.value, StatusAgendamento.FALTA.value):
            inicio = datetime.combine(agendamento.data, agendamento.hora_inicio)
            if inicio > self.relogio():
                raise RegraNegocioError(
                    "Não é possível marcar como realizado ou falta um agendamento futuro."
                )
        agendamento.status = novo_status
        self.db.commit()
        self.db.refresh(agendamento)
        return agendamento
