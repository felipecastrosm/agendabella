"""Hash de senhas (Argon2id) e tokens de sessão (JWT).

Senhas nunca são armazenadas em texto limpo nem com MD5/SHA-1. O hash é de
mão única: no login apenas recalculamos e comparamos, sem recuperar a senha.
"""

from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Papel, Profissional
from app.repositories import ProfissionalRepository

_hasher = PasswordHasher()  # Argon2id com salt aleatório e parâmetros recomendados
_bearer = HTTPBearer(auto_error=False)

TAMANHO_MINIMO_SENHA = 10


def gerar_hash(senha: str) -> str:
    if len(senha) < TAMANHO_MINIMO_SENHA:
        raise ValueError(f"A senha deve ter no mínimo {TAMANHO_MINIMO_SENHA} caracteres.")
    return _hasher.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return _hasher.verify(senha_hash, senha)
    except (VerificationError, InvalidHashError):
        return False


def criar_token(profissional: Profissional, agora: datetime | None = None) -> str:
    agora = agora or datetime.now(UTC)
    payload = {
        "sub": str(profissional.id),
        "papel": profissional.papel,
        "iat": agora,
        "exp": agora + timedelta(hours=settings.jwt_expiracao_horas),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algoritmo)


_NAO_AUTORIZADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Sessão inválida ou expirada. Faça login novamente.",
    headers={"WWW-Authenticate": "Bearer"},
)


def profissional_autenticada(
    credenciais: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Profissional:
    """Dependência aplicada a todas as rotas do painel: valida token e usuária ativa."""
    if credenciais is None:
        raise _NAO_AUTORIZADO
    try:
        payload = jwt.decode(
            credenciais.credentials, settings.jwt_secret, algorithms=[settings.jwt_algoritmo]
        )
        id_profissional = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _NAO_AUTORIZADO from None
    profissional = ProfissionalRepository(db).obter_ativa(id_profissional)
    if profissional is None:
        raise _NAO_AUTORIZADO
    return profissional


def exigir_proprietaria(
    profissional: Profissional = Depends(profissional_autenticada),
) -> Profissional:
    if profissional.papel != Papel.PROPRIETARIA.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso restrito à proprietária.")
    return profissional
