"""Detecção de ambientes em código JavaScript."""

from __future__ import annotations

import re
from typing import Any

from online.ambiente import normalizar_ambiente


_PADRAO_IMPORT_META_PROD = re.compile(
    r"\bimport\s*\.\s*meta\s*\.\s*env\s*\.\s*PROD\b",
    re.IGNORECASE,
)

_PADRAO_IMPORT_META_DEV = re.compile(
    r"\bimport\s*\.\s*meta\s*\.\s*env\s*\.\s*DEV\b",
    re.IGNORECASE,
)

_PADRAO_VARIAVEL_AMBIENTE = re.compile(
    r"(?<!\.)\b(?:environment|env|environment_name|env_name)\b"
    r"\s*=\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)

_PADRAO_PROPRIEDADE_AMBIENTE = re.compile(
    r"\b(?:config|configuration|settings|options)\b"
    r"\s*\.\s*"
    r"(?:environment|env)"
    r"\s*=\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)

_PADRAO_OBJETO_AMBIENTE = re.compile(
    r"\b(?:environment|env)\b"
    r"\s*:\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)

_PADRAO_COMPARACAO_NODE_ENV = re.compile(
    r"""\bprocess\s*\.\s*env\s*\.\s*NODE_ENV
    \s*(?:===|!==|==|!=)
    \s*["']([^"']+)["']""",
    re.IGNORECASE | re.VERBOSE,
)

_PADROES_COMENTARIO = (
    re.compile(r"//[^\n]*"),
    re.compile(r"/\*.*?\*/", re.DOTALL),
)

_CLASSIFICACOES_VALIDAS = {"possivel", "provavel", "confirmado"}


def _mascarar_comentarios(codigo: str) -> str:
    """Mascara comentários preservando o tamanho original."""
    mascarado = codigo

    for padrao in _PADROES_COMENTARIO:
        mascarado = padrao.sub(
            lambda match: "".join(
                "\n" if caractere == "\n" else " "
                for caractere in match.group(0)
            ),
            mascarado,
        )

    return mascarado


def _intervalos_strings(codigo: str) -> list[tuple[int, int]]:
    """Retorna intervalos de strings simples preservando offsets."""
    intervalos: list[tuple[int, int]] = []
    inicio: int | None = None
    delimitador = ""
    escape = False

    for indice, caractere in enumerate(codigo):
        if inicio is None:
            if caractere in {"'", '"', "`"}:
                inicio = indice
                delimitador = caractere
                escape = False
            continue

        if escape:
            escape = False
            continue

        if caractere == "\\":
            escape = True
            continue

        if caractere == delimitador:
            intervalos.append((inicio, indice + 1))
            inicio = None
            delimitador = ""
            escape = False

    if inicio is not None:
        intervalos.append((inicio, len(codigo)))

    return intervalos


def _esta_em_string(inicio: int, intervalos: list[tuple[int, int]]) -> bool:
    """Indica se uma ocorrência começa dentro de uma string."""
    return any(
        inicio_intervalo <= inicio < fim_intervalo
        for inicio_intervalo, fim_intervalo in intervalos
    )


def _localizacao(codigo: str, inicio: int) -> dict[str, int]:
    """Calcula linha e coluna de uma ocorrência."""
    linha = codigo.count("\n", 0, inicio) + 1
    ultimo_nova_linha = codigo.rfind("\n", 0, inicio)
    coluna = inicio + 1 if ultimo_nova_linha == -1 else inicio - ultimo_nova_linha

    return {
        "linha": linha,
        "coluna": coluna,
    }


def _normalizar_classificacao(valor: str) -> str:
    valor = valor.strip().lower()

    if valor in _CLASSIFICACOES_VALIDAS:
        return valor

    return "provavel"


def _criar_observacao(
    *,
    ambiente: str,
    origem: str,
    arquivo: str,
    tipo: str,
    codigo: str,
    inicio: int,
    evidencias: list[str] | None = None,
    pontuacao: int = 80,
    confianca: str = "MEDIA",
    valor_original: str | None = None,
    interpretacao: str | None = None,
) -> dict[str, Any]:
    ambiente_normalizado = normalizar_ambiente(ambiente)

    if not ambiente_normalizado:
        raise ValueError("ambiente vazio")

    localizacao = _localizacao(codigo, inicio)

    resultado: dict[str, Any] = {
        "ambiente": ambiente_normalizado,
        "valor_original": valor_original or ambiente,
        "origem": origem,
        "arquivo": arquivo,
        "tipo": tipo,
        "localizacao": localizacao,
        "classificacao": _normalizar_classificacao(
            "confirmado" if tipo == "comparacao" else "provavel"
        ),
        "pontuacao": pontuacao,
        "confianca": confianca,
        "evidencias": evidencias or [],
    }

    if interpretacao:
        resultado["interpretacao"] = interpretacao

    return resultado


def _adicionar(
    resultados: list[dict[str, Any]],
    observacao: dict[str, Any],
) -> None:
    """Adiciona uma observação evitando duplicação exata."""
    chave = (
        observacao["ambiente"],
        observacao["tipo"],
        observacao["localizacao"]["linha"],
        observacao["localizacao"]["coluna"],
    )

    for existente in resultados:
        chave_existente = (
            existente["ambiente"],
            existente["tipo"],
            existente["localizacao"]["linha"],
            existente["localizacao"]["coluna"],
        )

        if chave == chave_existente:
            return

    resultados.append(observacao)


def detectar_ambientes(
    codigo: str,
    *,
    origem: str = "",
    arquivo: str = "",
    linguagem: str = "javascript",
) -> list[dict[str, Any]]:
    """Detecta ambientes explicitamente observados no código."""
    if not codigo:
        return []

    if linguagem.lower() not in {
        "javascript",
        "js",
        "jsx",
        "typescript",
        "ts",
        "tsx",
    }:
        return []

    mascarado = _mascarar_comentarios(codigo)
    intervalos_strings = _intervalos_strings(codigo)
    resultados: list[dict[str, Any]] = []

    for match in _PADRAO_COMPARACAO_NODE_ENV.finditer(mascarado):
        if _esta_em_string(match.start(), intervalos_strings):
            continue
        valor = match.group(1)
        ambiente = normalizar_ambiente(valor)

        if not ambiente:
            continue

        _adicionar(
            resultados,
            _criar_observacao(
                ambiente=ambiente,
                origem=origem,
                arquivo=arquivo,
                tipo="comparacao",
                codigo=codigo,
                inicio=match.start(),
                evidencias=["process.env.NODE_ENV"],
                pontuacao=95,
                confianca="ALTA",
                valor_original=valor,
            ),
        )

    for match in _PADRAO_IMPORT_META_PROD.finditer(mascarado):
        if _esta_em_string(match.start(), intervalos_strings):
            continue
        _adicionar(
            resultados,
            _criar_observacao(
                ambiente="production",
                origem=origem,
                arquivo=arquivo,
                tipo="import_meta_env_flag",
                codigo=codigo,
                inicio=match.start(),
                evidencias=["import.meta.env.PROD"],
                pontuacao=90,
                confianca="ALTA",
                valor_original="PROD",
                interpretacao="flag PROD observada; interpretação normalizada como production",
            ),
        )

    for match in _PADRAO_IMPORT_META_DEV.finditer(mascarado):
        if _esta_em_string(match.start(), intervalos_strings):
            continue
        _adicionar(
            resultados,
            _criar_observacao(
                ambiente="development",
                origem=origem,
                arquivo=arquivo,
                tipo="import_meta_env_flag",
                codigo=codigo,
                inicio=match.start(),
                evidencias=["import.meta.env.DEV"],
                pontuacao=90,
                confianca="ALTA",
                valor_original="DEV",
                interpretacao="flag DEV observada; interpretação normalizada como development",
            ),
        )

    for match in _PADRAO_VARIAVEL_AMBIENTE.finditer(mascarado):
        if _esta_em_string(match.start(), intervalos_strings):
            continue
        valor = match.group(1)
        ambiente = normalizar_ambiente(valor)

        if not ambiente:
            continue

        _adicionar(
            resultados,
            _criar_observacao(
                ambiente=ambiente,
                origem=origem,
                arquivo=arquivo,
                tipo="atribuicao_ambiente",
                codigo=codigo,
                inicio=match.start(),
                evidencias=["variavel_ambiente"],
                pontuacao=85,
                confianca="ALTA",
                valor_original=valor,
            ),
        )

    for match in _PADRAO_PROPRIEDADE_AMBIENTE.finditer(mascarado):
        if _esta_em_string(match.start(), intervalos_strings):
            continue
        valor = match.group(1)
        ambiente = normalizar_ambiente(valor)

        if not ambiente:
            continue

        _adicionar(
            resultados,
            _criar_observacao(
                ambiente=ambiente,
                origem=origem,
                arquivo=arquivo,
                tipo="propriedade_ambiente",
                codigo=codigo,
                inicio=match.start(),
                evidencias=["propriedade_ambiente"],
                pontuacao=90,
                confianca="ALTA",
                valor_original=valor,
            ),
        )

    for match in _PADRAO_OBJETO_AMBIENTE.finditer(mascarado):
        if _esta_em_string(match.start(), intervalos_strings):
            continue
        valor = match.group(1)
        ambiente = normalizar_ambiente(valor)

        if not ambiente:
            continue

        _adicionar(
            resultados,
            _criar_observacao(
                ambiente=ambiente,
                origem=origem,
                arquivo=arquivo,
                tipo="objeto_ambiente",
                codigo=codigo,
                inicio=match.start(),
                evidencias=["campo_ambiente"],
                pontuacao=85,
                confianca="ALTA",
                valor_original=valor,
            ),
        )

    resultados.sort(
        key=lambda item: (
            item["localizacao"]["linha"],
            item["localizacao"]["coluna"],
        )
    )

    return resultados
