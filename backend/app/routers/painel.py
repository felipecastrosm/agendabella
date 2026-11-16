"""Rotas do painel da equipe (RF04 e RF05). Todas exigem token válido."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Profissional
from app.repositories import AgendamentoRepository, ProfissionalRepository
from app.schemas import AgendaOut, AgendaProfissional, AgendamentoPainel, StatusIn
from app.security import profissional_autenticada
from app.services.agendamento_service import (
    AgendamentoService,
    RecursoNaoEncontrado,
    RegraNegocioError,
)

router = APIRouter(
    prefix="/api/painel",
    tags=["painel"],
    dependencies=[Depends(profissional_autenticada)],
)


def get_agendamento_service(db: Session = Depends(get_db)) -> AgendamentoService:
    return AgendamentoService(db)


def _para_painel(ag) -> AgendamentoPainel:
    return AgendamentoPainel(
        id=ag.id,
        data=ag.data,
        hora_inicio=ag.hora_inicio.strftime("%H:%M"),
        hora_fim=ag.hora_fim.strftime("%H:%M"),
        status=ag.status,
        cliente=ag.cliente.nome,
        telefone=ag.cliente.telefone,
        servico=ag.servico.nome,
        id_profissional=ag.id_profissional,
        profissional=ag.profissional.nome,
    )


@router.get("/agenda", response_model=AgendaOut)
def agenda(
    data: date = Query(default_factory=date.today),
    dias: int = Query(default=1, ge=1, le=7),
    db: Session = Depends(get_db),
):
    """RF04: agenda do dia (dias=1) ou da semana (dias=7), organizada por profissional."""
    fim = data + timedelta(days=dias - 1)
    agendamentos = AgendamentoRepository(db).listar_periodo(data, fim)
    grupos = []
    for prof in ProfissionalRepository(db).listar_ativas():
        itens = [_para_painel(a) for a in agendamentos if a.id_profissional == prof.id]
        grupos.append(AgendaProfissional(id_profissional=prof.id, profissional=prof.nome, agendamentos=itens))
    return AgendaOut(inicio=data, fim=fim, profissionais=grupos)


@router.patch("/agendamentos/{id_agendamento}", response_model=AgendamentoPainel)
def alterar_status(
    id_agendamento: int,
    dados: StatusIn,
    _: Profissional = Depends(profissional_autenticada),
    service: AgendamentoService = Depends(get_agendamento_service),
):
    """RF05: marca o agendamento como realizado, falta ou cancelado."""
    try:
        ag = service.alterar_status(id_agendamento, dados.status)
    except RecursoNaoEncontrado as erro:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(erro)) from None
    except RegraNegocioError as erro:
        raise HTTPException(422, str(erro)) from None
    return _para_painel(ag)
