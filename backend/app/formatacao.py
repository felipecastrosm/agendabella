"""Funções de formatação compartilhadas entre camadas (sem regras de negócio)."""

from datetime import time


def hhmm(hora: time) -> str:
    """Formata um horário no padrão exibido ao usuário: "14:00"."""
    return hora.strftime("%H:%M")


def lista_hhmm(horas: list[time], limite: int | None = None) -> list[str]:
    selecionadas = horas if limite is None else horas[:limite]
    return [hhmm(h) for h in selecionadas]
