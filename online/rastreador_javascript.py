from __future__ import annotations

from typing import Any


def explicar_cadeia_variaveis(
    cadeia: list[str],
) -> dict[str, Any]:
    """
    Explica uma cadeia de propagação de variáveis JavaScript.

    Exemplo:

        ["resposta", "dados", "corpo", "valor"]

    produz:

        resposta
           ↓
        dados
           ↓
        corpo
           ↓
        valor
    """

    if not cadeia:
        return {
            "origem": None,
            "destino": None,
            "total_etapas": 0,
            "cadeia": [],
            "fluxo_visual": "",
        }

    return {
        "origem": cadeia[0],
        "destino": cadeia[-1],
        "total_etapas": max(len(cadeia) - 1, 0),
        "cadeia": list(cadeia),
        "fluxo_visual": "\n   ↓\n".join(cadeia),
    }
