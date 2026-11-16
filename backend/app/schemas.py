"""Esquemas Pydantic: validação de entrada no servidor e formato das respostas."""

import re
from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Letras (inclusive acentuadas), espaço, hífen e apóstrofo — rejeita tags e símbolos (OWASP A03).
PADRAO_NOME = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ' -]{2,80}$")


def normalizar_telefone(valor: str) -> str:
    """Remove espaços, parênteses e hífens e valida DDD + número (10 ou 11 dígitos)."""
    digitos = re.sub(r"[\s()\-]", "", valor or "")
    if not digitos.isdigit() or len(digitos) not in (10, 11):
        raise ValueError("Informe o telefone com DDD, ex.: 21 90000-0000.")
    if not 11 <= int(digitos[:2]) <= 99:
        raise ValueError("DDD inválido. Informe o telefone com DDD, ex.: 21 90000-0000.")
    return digitos


class ServicoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    duracao_minutos: int
    preco: float


class ProfissionalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str


class HorariosOut(BaseModel):
    data: date
    id_profissional: int
    id_servico: int
    horarios: list[str]


class AgendamentoIn(BaseModel):
    id_servico: int = Field(gt=0)
    id_profissional: int = Field(gt=0)
    data: date
    hora_inicio: time
    nome: str
    telefone: str

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        valor = " ".join(valor.split())
        if not PADRAO_NOME.match(valor):
            raise ValueError("Informe seu nome usando apenas letras (mínimo de 2 caracteres).")
        return valor

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, valor: str) -> str:
        return normalizar_telefone(valor)


class AgendamentoConfirmado(BaseModel):
    id: int
    servico: str
    profissional: str
    data: date
    hora_inicio: str
    hora_fim: str
    status: str


class ConflitoOut(BaseModel):
    mensagem: str
    alternativas: list[str]


class LoginIn(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    senha: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nome: str
    papel: str


class AgendamentoPainel(BaseModel):
    id: int
    data: date
    hora_inicio: str
    hora_fim: str
    status: str
    cliente: str
    telefone: str
    servico: str
    id_profissional: int
    profissional: str


class AgendaProfissional(BaseModel):
    id_profissional: int
    profissional: str
    agendamentos: list[AgendamentoPainel]


class AgendaOut(BaseModel):
    inicio: date
    fim: date
    profissionais: list[AgendaProfissional]


class StatusIn(BaseModel):
    status: Literal["realizado", "falta", "cancelado"]
