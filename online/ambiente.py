"""Normalização de nomes de ambientes observados."""

from __future__ import annotations


_ALIASES_AMBIENTE = {
    "production": "production",
    "prod": "production",
    "development": "development",
    "develop": "development",
    "dev": "development",
    "staging": "staging",
    "stage": "staging",
    "testing": "test",
    "test": "test",
}


def normalizar_ambiente(valor: str | None) -> str:
    """Normaliza um nome de ambiente sem inventar classificações.

    Valores conhecidos são convertidos para uma forma canônica.
    Valores desconhecidos são preservados em minúsculas, após limpeza.
    """
    if valor is None:
        return ""

    texto = str(valor).strip().lower()

    if not texto:
        return ""

    return _ALIASES_AMBIENTE.get(texto, texto)
