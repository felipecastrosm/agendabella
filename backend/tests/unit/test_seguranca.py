"""Testes unitários de hash de senhas, tokens e bloqueio de tentativas (RF03, RNF01)."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config import settings
from app.models import Profissional
from app.security import criar_token, gerar_hash, verificar_senha
from app.services.auth_service import ControleTentativas


def test_hash_usa_argon2id_e_nao_contem_a_senha():
    senha = "senha-forte-123"
    valor = gerar_hash(senha)
    assert valor.startswith("$argon2id$")
    assert senha not in valor


def test_hashes_diferentes_para_a_mesma_senha_por_causa_do_salt():
    assert gerar_hash("senha-forte-123") != gerar_hash("senha-forte-123")


def test_verificacao_de_senha():
    valor = gerar_hash("senha-forte-123")
    assert verificar_senha("senha-forte-123", valor)
    assert not verificar_senha("senha-errada-000", valor)
    assert not verificar_senha("qualquer", "nao-e-um-hash")


def test_rejeita_senha_curta():
    with pytest.raises(ValueError):
        gerar_hash("curta")


def test_token_contem_apenas_id_e_papel_e_expira_em_8h():
    prof = Profissional(id=7, papel="proprietaria")
    agora = datetime(2026, 11, 23, 8, 0, tzinfo=UTC)
    token = criar_token(prof, agora=agora)
    payload = jwt.decode(
        token, settings.jwt_secret, algorithms=[settings.jwt_algoritmo], options={"verify_exp": False, "verify_iat": False}
    )
    assert payload["sub"] == "7" and payload["papel"] == "proprietaria"
    assert payload["exp"] - payload["iat"] == 8 * 3600
    assert "email" not in payload and "nome" not in payload


def test_bloqueio_apos_cinco_falhas_e_liberacao_apos_janela():
    agora = [datetime(2026, 11, 23, 8, 0)]
    controle = ControleTentativas(5, 15, relogio=lambda: agora[0])
    for _ in range(5):
        controle.registrar_falha("ana@studiobella.test")
    assert controle.bloqueado("ana@studiobella.test")
    agora[0] += timedelta(minutes=16)
    assert not controle.bloqueado("ana@studiobella.test")
