"""Testes de integração das rotas públicas (API + serviço + banco)."""

from tests.conftest import TERCA


def _payload(dados, **extra):
    base = {
        "id_servico": dados["escova"].id,
        "id_profissional": dados["ana"].id,
        "data": TERCA.isoformat(),
        "hora_inicio": "14:00",
        "nome": "Joana Souza",
        "telefone": "21 90000-0000",
    }
    base.update(extra)
    return base


def test_saude(client):
    assert client.get("/api/saude").json() == {"status": "ok"}


def test_lista_apenas_servicos_ativos(client, dados):
    nomes = [s["nome"] for s in client.get("/api/servicos").json()]
    assert "Escova" in nomes and "Serviço antigo" not in nomes


def test_lista_profissionais_sem_dados_sensiveis(client, dados):
    profissionais = client.get("/api/profissionais").json()
    assert {"id", "nome"} == set(profissionais[0].keys())


def test_horarios_disponiveis(client, dados):
    resp = client.get(
        "/api/horarios-disponiveis",
        params={"id_servico": dados["escova"].id, "id_profissional": dados["ana"].id, "data": TERCA},
    )
    assert resp.status_code == 200
    assert resp.json()["horarios"][0] == "09:00"


def test_horarios_profissional_inexistente_retorna_404(client, dados):
    resp = client.get(
        "/api/horarios-disponiveis",
        params={"id_servico": dados["escova"].id, "id_profissional": 999, "data": TERCA},
    )
    assert resp.status_code == 404


def test_fluxo_completo_de_agendamento(client, dados):
    resp = client.post("/api/agendamentos", json=_payload(dados))
    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["servico"] == "Escova" and corpo["hora_fim"] == "14:45"

    horarios = client.get(
        "/api/horarios-disponiveis",
        params={"id_servico": dados["escova"].id, "id_profissional": dados["ana"].id, "data": TERCA},
    ).json()["horarios"]
    assert "14:00" not in horarios


def test_conflito_retorna_409_com_alternativas(client, dados):
    client.post("/api/agendamentos", json=_payload(dados))
    resp = client.post("/api/agendamentos", json=_payload(dados, telefone="21 91111-1111"))
    assert resp.status_code == 409
    assert resp.json()["alternativas"]
    assert "acabou de ser reservado" in resp.json()["mensagem"]


def test_telefone_invalido_retorna_mensagem_com_correcao(client, dados):
    resp = client.post("/api/agendamentos", json=_payload(dados, telefone="2190000"))
    assert resp.status_code == 422
    assert "Informe o telefone com DDD" in resp.json()["detail"][0]


def test_rejeita_nome_com_html(client, dados):
    resp = client.post(
        "/api/agendamentos", json=_payload(dados, nome="<script>alert(1)</script>")
    )
    assert resp.status_code == 422


def test_tentativa_de_injecao_sql_e_tratada_como_texto(client, dados):
    resp = client.post("/api/agendamentos", json=_payload(dados, nome="Ana' OR 1=1 --"))
    assert resp.status_code == 422  # caracteres não permitidos são rejeitados
    assert client.get("/api/servicos").status_code == 200  # base intacta
