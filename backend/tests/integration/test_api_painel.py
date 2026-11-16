"""Testes de integração do login e do painel da equipe (RF03, RF04, RF05)."""

from datetime import datetime, time

import pytest

from app.routers import auth as auth_router
from app.routers import painel as painel_router
from app.security import gerar_hash
from app.services.agendamento_service import AgendamentoService
from app.services.auth_service import AuthService, ControleTentativas
from tests.conftest import AGORA, TERCA, relogio_fixo

SENHA = "senha-demo-123"


@pytest.fixture
def equipe(db, dados):
    for prof in (dados["ana"], dados["marcia"]):
        prof.senha_hash = gerar_hash(SENHA)
    db.commit()
    return dados


@pytest.fixture
def api(client, db, equipe):
    controle = ControleTentativas(5, 15, relogio=relogio_fixo)
    client.app.dependency_overrides[auth_router.get_auth_service] = lambda: AuthService(db, controle)
    client.app.dependency_overrides[painel_router.get_agendamento_service] = (
        lambda: AgendamentoService(db, relogio=relogio_fixo)
    )
    return client


def _token(api, email="ana@studiobella.test", senha=SENHA):
    resp = api.post("/api/auth/login", json={"email": email, "senha": senha})
    return resp


def _auth(api):
    return {"Authorization": f"Bearer {_token(api).json()['access_token']}"}


def _agendar(api, equipe, hora="14:00", telefone="21 90000-0000"):
    return api.post(
        "/api/agendamentos",
        json={
            "id_servico": equipe["escova"].id,
            "id_profissional": equipe["ana"].id,
            "data": TERCA.isoformat(),
            "hora_inicio": hora,
            "nome": "Joana Souza",
            "telefone": telefone,
        },
    ).json()


def test_login_valido_retorna_token(api):
    resp = _token(api)
    assert resp.status_code == 200
    assert resp.json()["nome"] == "Ana" and resp.json()["access_token"]


def test_login_invalido_tem_mensagem_generica_igual_para_email_inexistente(api):
    errado = _token(api, senha="senha-errada-000")
    inexistente = _token(api, email="ninguem@studiobella.test")
    assert errado.status_code == inexistente.status_code == 401
    assert errado.json() == inexistente.json() == {"detail": "E-mail ou senha inválidos."}


def test_sexta_tentativa_invalida_e_bloqueada(api):
    for _ in range(5):
        assert _token(api, senha="senha-errada-000").status_code == 401
    assert _token(api).status_code == 429  # bloqueada mesmo com a senha correta


def test_painel_sem_token_retorna_401(api):
    assert api.get("/api/painel/agenda").status_code == 401


def test_painel_com_token_adulterado_retorna_401(api):
    token = _token(api).json()["access_token"] + "x"
    resp = api.get("/api/painel/agenda", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_agenda_do_dia_mostra_agendamento_criado_pela_cliente(api, equipe):
    _agendar(api, equipe)
    resp = api.get("/api/painel/agenda", params={"data": TERCA}, headers=_auth(api))
    assert resp.status_code == 200
    ana = next(p for p in resp.json()["profissionais"] if p["profissional"] == "Ana")
    assert ana["agendamentos"][0]["hora_inicio"] == "14:00"
    assert ana["agendamentos"][0]["cliente"] == "Joana Souza"


def test_agenda_da_semana(api, equipe):
    _agendar(api, equipe)
    resp = api.get(
        "/api/painel/agenda", params={"data": AGORA.date(), "dias": 7}, headers=_auth(api)
    )
    assert resp.json()["fim"] == "2026-11-29"


def test_cancelar_pelo_painel_libera_horario(api, equipe):
    ag = _agendar(api, equipe)
    resp = api.patch(
        f"/api/painel/agendamentos/{ag['id']}", json={"status": "cancelado"}, headers=_auth(api)
    )
    assert resp.status_code == 200 and resp.json()["status"] == "cancelado"
    horarios = api.get(
        "/api/horarios-disponiveis",
        params={"id_servico": equipe["escova"].id, "id_profissional": equipe["ana"].id, "data": TERCA},
    ).json()["horarios"]
    assert "14:00" in horarios


def test_marcar_falta_em_agendamento_futuro_retorna_422(api, equipe):
    ag = _agendar(api, equipe)
    resp = api.patch(
        f"/api/painel/agendamentos/{ag['id']}", json={"status": "falta"}, headers=_auth(api)
    )
    assert resp.status_code == 422


def test_marcar_realizado_apos_horario(api, db, equipe):
    ag = _agendar(api, equipe, hora="09:00")
    api.app.dependency_overrides[painel_router.get_agendamento_service] = lambda: AgendamentoService(
        db, relogio=lambda: datetime.combine(TERCA, time(10, 0))
    )
    resp = api.patch(
        f"/api/painel/agendamentos/{ag['id']}", json={"status": "realizado"}, headers=_auth(api)
    )
    assert resp.json()["status"] == "realizado"


def test_status_invalido_e_rejeitado(api, equipe):
    ag = _agendar(api, equipe)
    resp = api.patch(
        f"/api/painel/agendamentos/{ag['id']}", json={"status": "apagado"}, headers=_auth(api)
    )
    assert resp.status_code == 422


def test_alterar_agendamento_inexistente_retorna_404(api, equipe):
    resp = api.patch("/api/painel/agendamentos/999", json={"status": "cancelado"}, headers=_auth(api))
    assert resp.status_code == 404
