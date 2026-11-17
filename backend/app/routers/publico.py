"""Rotas públicas usadas pela cliente (sem login). Nunca expõem dados de outras clientes."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.formatacao import lista_hhmm
from app.repositories import ProfissionalRepository, ServicoRepository
from app.schemas import (
    AgendamentoConfirmado,
    AgendamentoIn,
    ConflitoOut,
    HorariosOut,
    ProfissionalOut,
    ProximoDiaOut,
    ServicoOut,
)
from app.services.agendamento_service import (
    AgendamentoService,
    ConflitoHorario,
    RecursoNaoEncontrado,
)

router = APIRouter(prefix="/api", tags=["público"])


def get_agendamento_service(db: Session = Depends(get_db)) -> AgendamentoService:
    return AgendamentoService(db)


@router.get("/servicos", response_model=list[ServicoOut])
def listar_servicos(db: Session = Depends(get_db)):
    return ServicoRepository(db).listar_ativos()


@router.get("/profissionais", response_model=list[ProfissionalOut])
def listar_profissionais(db: Session = Depends(get_db)):
    return ProfissionalRepository(db).listar_ativas()


@router.get("/horarios-disponiveis", response_model=HorariosOut)
def horarios_disponiveis(
    id_servico: int = Query(gt=0),
    id_profissional: int = Query(gt=0),
    data: date = Query(),
    service: AgendamentoService = Depends(get_agendamento_service),
):
    try:
        horarios = service.horarios_disponiveis(id_servico, id_profissional, data)
    except RecursoNaoEncontrado as erro:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(erro)) from None
    return HorariosOut(
        data=data,
        id_profissional=id_profissional,
        id_servico=id_servico,
        horarios=lista_hhmm(horarios),
    )


@router.get("/proximo-dia-disponivel", response_model=ProximoDiaOut)
def proximo_dia_disponivel(
    id_servico: int = Query(gt=0),
    id_profissional: int = Query(gt=0),
    a_partir_de: date = Query(),
    service: AgendamentoService = Depends(get_agendamento_service),
):
    try:
        dia = service.proximo_dia_disponivel(id_servico, id_profissional, a_partir_de)
    except RecursoNaoEncontrado as erro:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(erro)) from None
    return ProximoDiaOut(data=dia)


@router.post(
    "/agendamentos",
    response_model=AgendamentoConfirmado,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ConflitoOut}},
)
def criar_agendamento(
    dados: AgendamentoIn,
    service: AgendamentoService = Depends(get_agendamento_service),
):
    try:
        ag = service.agendar(
            dados.id_servico,
            dados.id_profissional,
            dados.data,
            dados.hora_inicio,
            dados.nome,
            dados.telefone,
        )
    except RecursoNaoEncontrado as erro:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(erro)) from None
    except ConflitoHorario as conflito:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ConflitoOut(mensagem=str(conflito), alternativas=conflito.alternativas).model_dump(),
        )
    return AgendamentoConfirmado.de_modelo(ag)
