"""Rota de login da equipe (RF03)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import LoginIn, TokenOut
from app.security import criar_token
from app.services.auth_service import AuthService, ContaBloqueada, CredenciaisInvalidas

router = APIRouter(prefix="/api/auth", tags=["autenticação"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/login", response_model=TokenOut)
def login(dados: LoginIn, service: AuthService = Depends(get_auth_service)):
    try:
        profissional = service.autenticar(dados.email, dados.senha)
    except ContaBloqueada as erro:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(erro)) from None
    except CredenciaisInvalidas as erro:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(erro)) from None
    return TokenOut(
        access_token=criar_token(profissional), nome=profissional.nome, papel=profissional.papel
    )
