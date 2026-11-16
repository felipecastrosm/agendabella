"""Testes da camada de serviço com banco em memória (RF02 e RF05)."""

from datetime import time

import pytest

from app.models import Agendamento, Cliente
from app.services.agendamento_service import (
    AgendamentoService,
    ConflitoHorario,
    RecursoNaoEncontrado,
    RegraNegocioError,
)
from tests.conftest import TERCA, relogio_fixo


@pytest.fixture
def service(db):
    return AgendamentoService(db, relogio=relogio_fixo)


def _agendar(service, dados, hora, telefone="21900000000", servico="corte"):
    return service.agendar(
        dados[servico].id, dados["ana"].id, TERCA, hora, "Joana Souza", telefone
    )


def test_agendamento_valido_calcula_hora_fim(service, dados):
    ag = _agendar(service, dados, time(14, 0))
    assert ag.hora_fim == time(15, 0)
    assert ag.status == "confirmado"


def test_impede_mesmo_horario(service, dados):
    _agendar(service, dados, time(14, 0))
    with pytest.raises(ConflitoHorario) as erro:
        _agendar(service, dados, time(14, 0), telefone="21911111111")
    assert "14:00" not in erro.value.alternativas
    assert erro.value.alternativas  # oferece horários alternativos


def test_impede_sobreposicao_parcial(service, dados):
    _agendar(service, dados, time(14, 0))  # 14:00-15:00
    with pytest.raises(ConflitoHorario):
        _agendar(service, dados, time(14, 30), telefone="21911111111", servico="escova")


def test_permite_horario_imediatamente_apos(service, dados):
    _agendar(service, dados, time(14, 0))
    ag = _agendar(service, dados, time(15, 0), telefone="21911111111")
    assert ag.hora_inicio == time(15, 0)


def test_reaproveita_cliente_pelo_telefone(service, dados, db):
    _agendar(service, dados, time(9, 0))
    _agendar(service, dados, time(11, 0))
    assert db.query(Cliente).count() == 1
    assert db.query(Agendamento).count() == 2


def test_servico_inativo_nao_pode_ser_agendado(service, dados):
    with pytest.raises(RecursoNaoEncontrado):
        _agendar(service, dados, time(9, 0), servico="inativo")


def test_cancelamento_libera_horario(service, dados):
    ag = _agendar(service, dados, time(14, 0))
    service.alterar_status(ag.id, "cancelado")
    livres = service.horarios_disponiveis(dados["corte"].id, dados["ana"].id, TERCA)
    assert time(14, 0) in livres


def test_agendamento_cancelado_nao_pode_ser_reativado(service, dados):
    ag = _agendar(service, dados, time(14, 0))
    service.alterar_status(ag.id, "cancelado")
    _agendar(service, dados, time(14, 0), telefone="21911111111")  # outra cliente ocupa o horário
    with pytest.raises(RegraNegocioError):
        service.alterar_status(ag.id, "realizado")


def test_nao_marca_falta_em_agendamento_futuro(service, dados):
    ag = _agendar(service, dados, time(14, 0))
    with pytest.raises(RegraNegocioError):
        service.alterar_status(ag.id, "falta")


def test_marca_realizado_apos_o_horario(db, dados):
    from datetime import datetime

    ag = AgendamentoService(db, relogio=relogio_fixo).agendar(
        dados["corte"].id, dados["ana"].id, TERCA, time(9, 0), "Joana Souza", "21900000000"
    )
    depois = AgendamentoService(db, relogio=lambda: datetime.combine(TERCA, time(10, 0)))
    assert depois.alterar_status(ag.id, "realizado").status == "realizado"
