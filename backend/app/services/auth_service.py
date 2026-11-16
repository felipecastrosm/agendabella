"""Autenticação da equipe com bloqueio temporário após tentativas repetidas (RF03)."""

from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Profissional
from app.repositories import ProfissionalRepository
from app.security import verificar_senha

MENSAGEM_GENERICA = "E-mail ou senha inválidos."


class CredenciaisInvalidas(Exception):
    pass


class ContaBloqueada(Exception):
    pass


class ControleTentativas:
    """Registra falhas por e-mail e bloqueia após N falhas dentro da janela (OWASP A07)."""

    def __init__(self, maximo: int, janela_minutos: int, relogio: Callable[[], datetime]):
        self.maximo = maximo
        self.janela = timedelta(minutes=janela_minutos)
        self.relogio = relogio
        self._falhas: dict[str, list[datetime]] = defaultdict(list)

    def _recentes(self, email: str) -> list[datetime]:
        limite = self.relogio() - self.janela
        self._falhas[email] = [t for t in self._falhas[email] if t > limite]
        return self._falhas[email]

    def bloqueado(self, email: str) -> bool:
        return len(self._recentes(email)) >= self.maximo

    def registrar_falha(self, email: str) -> None:
        self._recentes(email).append(self.relogio())

    def limpar(self, email: str) -> None:
        self._falhas.pop(email, None)


controle_global = ControleTentativas(
    settings.max_falhas_login, settings.janela_bloqueio_minutos, datetime.now
)


class AuthService:
    def __init__(self, db: Session, controle: ControleTentativas = controle_global):
        self.repo = ProfissionalRepository(db)
        self.controle = controle

    def autenticar(self, email: str, senha: str) -> Profissional:
        email = email.strip().lower()
        if self.controle.bloqueado(email):
            raise ContaBloqueada(
                "Muitas tentativas sem sucesso. Aguarde 15 minutos e tente novamente."
            )
        profissional = self.repo.obter_por_email(email)
        valido = (
            profissional is not None
            and profissional.ativo
            and verificar_senha(senha, profissional.senha_hash)
        )
        if not valido:
            self.controle.registrar_falha(email)
            raise CredenciaisInvalidas(MENSAGEM_GENERICA)
        self.controle.limpar(email)
        return profissional
