"""Ajuste da 1ª rodada de validação: abrir a tela no primeiro dia com horário livre."""

from datetime import date, time

from app.services.agendamento_service import AgendamentoService
from tests.conftest import AGORA, TERCA, relogio_fixo


def test_pula_segunda_feira_sem_atendimento(client, dados):
    # AGORA é segunda-feira (salão fechado): deve sugerir a terça.
    resp = client.get(
        "/api/proximo-dia-disponivel",
        params={"id_servico": dados["escova"].id, "id_profissional": dados["ana"].id, "a_partir_de": AGORA.date()},
    )
    assert resp.status_code == 200
    assert resp.json() == {"data": TERCA.isoformat()}


def test_pula_dia_com_agenda_lotada(db, dados):
    servico = dados["corte"]  # 60 min
    service = AgendamentoService(db, relogio=relogio_fixo)
    for i, hora in enumerate(range(9, 18)):  # ocupa a terça das 9h às 18h
        service.agendar(servico.id, dados["ana"].id, TERCA, time(hora, 0), "Cliente Teste", f"2190000{i:04d}")
    assert service.proximo_dia_disponivel(servico.id, dados["ana"].id, AGORA.date()) == date(2026, 11, 25)


def test_retorna_nulo_quando_profissional_nao_atende_no_periodo(db, dados):
    dados["ana"].dias_atendimento = ""
    db.commit()
    service = AgendamentoService(db, relogio=relogio_fixo)
    assert service.proximo_dia_disponivel(dados["escova"].id, dados["ana"].id, AGORA.date()) is None


def test_profissional_inexistente_retorna_404(client, dados):
    resp = client.get(
        "/api/proximo-dia-disponivel",
        params={"id_servico": dados["escova"].id, "id_profissional": 999, "a_partir_de": AGORA.date()},
    )
    assert resp.status_code == 404
