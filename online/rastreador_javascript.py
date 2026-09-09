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


def analisar_transformacoes_javascript(
    codigo: str,
) -> list[dict[str, Any]]:
    """
    Detecta transformações simples de dados em JavaScript.

    Atualmente reconhece:

        const dados = JSON.parse(resposta);

    e:

        const nome = dados.user.name;
    """

    import re

    if not codigo:
        return []

    resultado = []

    padrao_json_parse = re.compile(
        r"\b(?:const|let|var)\s+"
        r"([A-Za-z_$][\w$]*)\s*=\s*"
        r"JSON\.parse\(\s*"
        r"([A-Za-z_$][\w$]*)"
        r"\s*\)"
    )

    for correspondencia in padrao_json_parse.finditer(codigo):
        saida = correspondencia.group(1)
        entrada = correspondencia.group(2)

        resultado.append(
            (
                correspondencia.start(),
                {
                    "tipo": "transformacao",
                    "operacao": "JSON.parse",
                    "entrada": entrada,
                    "saida": saida,
                },
            )
        )

    padrao_propriedade = re.compile(
        r"\b(?:const|let|var)\s+"
        r"([A-Za-z_$][\w$]*)\s*=\s*"
        r"(?!JSON\.parse\b)"
        r"(?!xhr\.(?:response|responseText)\b)"
        r"([A-Za-z_$][\w$]*)"
        r"((?:\.[A-Za-z_$][\w$]*)+)"
    )

    for correspondencia in padrao_propriedade.finditer(codigo):
        saida = correspondencia.group(1)
        entrada = correspondencia.group(2)
        propriedades = correspondencia.group(3)

        propriedade = propriedades.lstrip(".")

        resultado.append(
            (
                correspondencia.start(),
                {
                    "tipo": "propriedade",
                    "operacao": (
                        f"{entrada}.{propriedade}"
                    ),
                    "entrada": entrada,
                    "propriedade": propriedade,
                    "saida": saida,
                },
            )
        )

    resultado.sort(key=lambda item: item[0])

    return [
        transformacao
        for _, transformacao in resultado
    ]
