"""Normalização segura de configurações observadas passivamente.

Este módulo não realiza requisições, autenticação ou acesso a arquivos
externos. Ele apenas normaliza informações que já foram coletadas pelo
analisador online.

Valores sensíveis nunca são armazenados em claro no resultado.
"""

from __future__ import annotations

import hashlib
from typing import Any


_CLASSIFICACOES_VALIDAS = {
    "possivel",
    "provavel",
    "confirmado",
}

_VALOR_REDACTED = "[REDACTED]"


def _normalizar_texto(valor: Any) -> str:
    """Converte um valor para texto sem deixar espaços externos."""
    if valor is None:
        return ""

    return str(valor).strip()


def _normalizar_localizacao(localizacao: Any) -> dict[str, Any] | None:
    """Normaliza a localização da evidência, quando disponível."""
    if localizacao is None:
        return None

    if not isinstance(localizacao, dict):
        return None

    resultado: dict[str, Any] = {}

    if "linha" in localizacao:
        resultado["linha"] = localizacao["linha"]

    if "coluna" in localizacao:
        resultado["coluna"] = localizacao["coluna"]

    return resultado or None


def _normalizar_evidencias(evidencias: Any) -> list[str]:
    """Mantém somente evidências textuais não vazias."""
    if evidencias is None:
        return []

    if isinstance(evidencias, str):
        evidencias = [evidencias]

    if not isinstance(evidencias, (list, tuple)):
        return []

    resultado = []

    for evidencia in evidencias:
        texto = _normalizar_texto(evidencia)

        if texto:
            resultado.append(texto)

    return resultado


def _fingerprint_sha256(valor: Any) -> str:
    """Gera fingerprint SHA-256 do valor original."""
    texto = "" if valor is None else str(valor)

    return hashlib.sha256(
        texto.encode("utf-8")
    ).hexdigest()


def normalizar_configuracao(
    *,
    nome: Any,
    valor: Any = None,
    origem: Any = "",
    fonte: Any = "",
    localizacao: Any = None,
    caminho: Any = "",
    contexto: Any = "",
    tipo: Any = "",
    sensivel: Any = False,
    classificacao: Any = "possivel",
    pontuacao: Any = 0,
    confianca: Any = "",
    evidencias: Any = None,
) -> dict[str, Any]:
    """Normaliza uma configuração observada passivamente.

    Regras principais:

    - ``nome`` é obrigatório.
    - ``classificacao`` deve ser uma das classificações permitidas.
    - ``pontuacao`` deve estar entre 0 e 100.
    - valores sensíveis são sempre protegidos.
    - valores sensíveis recebem fingerprint SHA-256.
    - a proveniência é preservada.
    - localização ausente permanece como ``None``.
    - nenhuma requisição ou operação externa é realizada.

    Em caso de entrada inválida, retorna ``{}``.
    """

    nome_normalizado = _normalizar_texto(nome)

    if not nome_normalizado:
        return {}

    classificacao_normalizada = _normalizar_texto(
        classificacao
    ).lower()

    if classificacao_normalizada not in _CLASSIFICACOES_VALIDAS:
        return {}

    try:
        pontuacao_normalizada = int(pontuacao)
    except (TypeError, ValueError):
        return {}

    if not 0 <= pontuacao_normalizada <= 100:
        return {}

    origem_normalizada = _normalizar_texto(origem)
    fonte_normalizada = _normalizar_texto(fonte)
    caminho_normalizado = _normalizar_texto(caminho)
    contexto_normalizado = _normalizar_texto(contexto)
    tipo_normalizado = _normalizar_texto(tipo)
    confianca_normalizada = _normalizar_texto(confianca).lower()

    sensivel_normalizado = bool(sensivel)

    evidencias_normalizadas = _normalizar_evidencias(
        evidencias
    )

    localizacao_normalizada = _normalizar_localizacao(
        localizacao
    )

    resultado: dict[str, Any] = {
        "nome": nome_normalizado,
        "valor": _VALOR_REDACTED
        if sensivel_normalizado
        else valor,
        "valor_protegido": sensivel_normalizado,
        "origem": origem_normalizada,
        "fonte": fonte_normalizada,
        "localizacao": localizacao_normalizada,
        "caminho": caminho_normalizado,
        "contexto": contexto_normalizado,
        "tipo": tipo_normalizado,
        "sensivel": sensivel_normalizado,
        "classificacao": classificacao_normalizada,
        "pontuacao": pontuacao_normalizada,
        "confianca": confianca_normalizada,
        "evidencias": evidencias_normalizadas,
    }

    if sensivel_normalizado:
        resultado["fingerprint"] = {
            "algoritmo": "sha256",
            "valor": _fingerprint_sha256(valor),
        }

    return resultado
