"""Garante que toda resposta da API sai com cabeçalhos de segurança (OWASP A05)."""

from tests.conftest import TERCA


def test_cabecalhos_em_rota_publica(client):
    resp = client.get("/api/saude")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert resp.headers["Cache-Control"] == "no-store"


def test_cabecalhos_tambem_em_respostas_de_erro(client, dados):
    resp = client.post("/api/agendamentos", json={"data": TERCA.isoformat()})
    assert resp.status_code == 422
    assert resp.headers["X-Content-Type-Options"] == "nosniff"


def test_resposta_publica_de_agendamento_nao_expoe_dados_da_cliente(client, dados):
    resp = client.post(
        "/api/agendamentos",
        json={
            "id_servico": dados["escova"].id,
            "id_profissional": dados["ana"].id,
            "data": TERCA.isoformat(),
            "hora_inicio": "10:00",
            "nome": "Joana Souza",
            "telefone": "21 90000-0000",
        },
    )
    assert resp.status_code == 201
    assert "telefone" not in resp.json() and "cliente" not in resp.json()
