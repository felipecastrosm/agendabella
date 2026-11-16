"""Testes unitários da função pura de cálculo de horários livres (RF01)."""

from datetime import datetime, time

from app.models import Profissional, Servico
from app.services.agendamento_service import Intervalo, calcular_horarios_livres, somar_minutos
from tests.conftest import AGORA, DOMINGO, TERCA


def _profissional():
    return Profissional(
        nome="Ana",
        dias_atendimento="1,2,3,4,5",
        hora_inicio_expediente=time(9, 0),
        hora_fim_expediente=time(18, 0),
    )


def _servico(minutos=60):
    return Servico(nome="Corte", duracao_minutos=minutos, preco=70)


def test_intervalos_sobrepostos_parcialmente():
    assert Intervalo(time(14, 0), time(15, 0)).sobrepoe(Intervalo(time(14, 30), time(15, 15)))


def test_intervalos_encostados_nao_se_sobrepoem():
    assert not Intervalo(time(14, 0), time(15, 0)).sobrepoe(Intervalo(time(15, 0), time(16, 0)))


def test_somar_minutos():
    assert somar_minutos(time(9, 45), 45) == time(10, 30)


def test_cenario_de_aceitacao_do_rf01():
    """Expediente 9h-18h, serviço de 60 min e agendamento existente às 14h (critério da Exp. 2)."""
    ocupados = [Intervalo(time(14, 0), time(15, 0))]
    livres = calcular_horarios_livres(_profissional(), _servico(60), TERCA, ocupados, AGORA)

    assert time(14, 0) not in livres
    assert time(13, 30) not in livres
    assert time(13, 0) in livres
    assert time(15, 0) in livres
    assert max(livres) == time(17, 0)  # nenhum horário que termine depois das 18h


def test_sem_horarios_em_dia_sem_atendimento():
    assert calcular_horarios_livres(_profissional(), _servico(), DOMINGO, [], AGORA) == []


def test_nao_oferece_horarios_no_passado_nem_sem_antecedencia():
    agora = datetime.combine(TERCA, time(10, 50))
    livres = calcular_horarios_livres(_profissional(), _servico(60), TERCA, [], agora)
    assert min(livres) == time(11, 30)  # 30 min de antecedência mínima, passo de 15 min


def test_servico_de_45_minutos_respeita_fim_do_expediente():
    livres = calcular_horarios_livres(_profissional(), _servico(45), TERCA, [], AGORA)
    assert livres[0] == time(9, 0)
    assert livres[-1] == time(17, 15)
