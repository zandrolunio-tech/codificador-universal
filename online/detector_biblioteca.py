"""
Detector de bibliotecas/pacotes observados em JavaScript e TypeScript.

O detector identifica referências explícitas a pacotes por meio de:
- import ... from "pacote"
- import "pacote"
- import("pacote")
- require("pacote")

Não tenta inferir bibliotecas a partir de símbolos isolados.
"""

from __future__ import annotations

import re
from typing import Any


_LINGUAGENS_SUPORTADAS = {
    "javascript",
    "typescript",
}


_PADROES_IMPORTACAO = (
    (
        "import",
        re.compile(
            r"(?<![\w$.])\bimport\s+(?:[\s\S]*?\s+from\s+)?"
            r"(?P<quote>[\"'])(?P<pacote>[^\"']+)(?P=quote)"
        ),
    ),
    (
        "dynamic_import",
        re.compile(
            r"(?<![\w$.])\bimport\s*\(\s*"
            r"(?P<quote>[\"'])(?P<pacote>[^\"']+)(?P=quote)"
            r"\s*\)"
        ),
    ),
    (
        "require",
        re.compile(
            r"(?<![\w$.])\brequire\s*\(\s*"
            r"(?P<quote>[\"'])(?P<pacote>[^\"']+)(?P=quote)"
            r"\s*\)"
        ),
    ),
)


def _normalizar_linguagem(linguagem: str | None) -> str:
    valor = (linguagem or "").strip().lower()

    aliases = {
        "js": "javascript",
        "jsx": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
    }

    return aliases.get(valor, valor)


def _linguagem_suportada(linguagem: str | None) -> bool:
    normalizada = _normalizar_linguagem(linguagem)

    return normalizada in _LINGUAGENS_SUPORTADAS


def _mascarar_comentarios(codigo: str) -> str:
    """
    Remove comentários preservando posições, linhas e colunas.

    Strings e template strings são preservadas durante esta etapa para
    evitar interpretar // ou /* dentro de strings como comentários.
    """
    resultado = list(codigo)
    i = 0
    tamanho = len(codigo)

    estado = "normal"
    quote = ""

    while i < tamanho:
        atual = codigo[i]
        proximo = codigo[i + 1] if i + 1 < tamanho else ""

        if estado == "normal":
            if atual in {"'", '"', "`"}:
                quote = atual
                estado = "string"
                i += 1
                continue

            if atual == "/" and proximo == "/":
                resultado[i] = " "
                resultado[i + 1] = " "
                i += 2
                estado = "linha"
                continue

            if atual == "/" and proximo == "*":
                resultado[i] = " "
                resultado[i + 1] = " "
                i += 2
                estado = "bloco"
                continue

            i += 1
            continue

        if estado == "string":
            if atual == "\\":
                i += 2
                continue

            if atual == quote:
                estado = "normal"
                quote = ""

            i += 1
            continue

        if estado == "linha":
            if atual == "\n":
                estado = "normal"
            else:
                resultado[i] = " "
            i += 1
            continue

        if estado == "bloco":
            if atual == "*" and proximo == "/":
                resultado[i] = " "
                resultado[i + 1] = " "
                i += 2
                estado = "normal"
                continue

            if atual != "\n":
                resultado[i] = " "

            i += 1
            continue

    return "".join(resultado)


def _mascarar_strings(codigo: str) -> str:
    """
    Mascara strings mantendo quebras de linha e posições.
    """
    resultado = list(codigo)
    i = 0
    tamanho = len(codigo)
    estado = "normal"
    quote = ""

    while i < tamanho:
        atual = codigo[i]

        if estado == "normal":
            if atual in {"'", '"', "`"}:
                quote = atual
                resultado[i] = " "
                estado = "string"
            i += 1
            continue

        if atual == "\\":
            resultado[i] = " "

            if i + 1 < tamanho:
                if codigo[i + 1] != "\n":
                    resultado[i + 1] = " "
                i += 2
            else:
                i += 1

            continue

        if atual == quote:
            resultado[i] = " "
            estado = "normal"
            quote = ""
            i += 1
            continue

        if atual != "\n":
            resultado[i] = " "

        i += 1

    return "".join(resultado)


def _mascarar_codigo(codigo: str) -> str:
    return _mascarar_strings(_mascarar_comentarios(codigo))


def _esta_em_string(codigo_mascarado: str, posicao: int) -> bool:
    """
    Verifica se a posição original está dentro de uma string.

    Em código totalmente mascarado, caracteres que estavam dentro de
    strings foram substituídos por espaços.
    """
    if posicao < 0 or posicao >= len(codigo_mascarado):
        return False

    return codigo_mascarado[posicao] == " "


def _localizacao(codigo: str, posicao: int) -> dict[str, int]:
    linha = codigo.count("\n", 0, posicao) + 1

    inicio_linha = codigo.rfind("\n", 0, posicao)

    if inicio_linha == -1:
        coluna = posicao + 1
    else:
        coluna = posicao - inicio_linha

    return {
        "linha": linha,
        "coluna": coluna,
    }


def _evidencia(codigo: str, posicao: int) -> str:
    inicio = codigo.rfind("\n", 0, posicao)

    if inicio == -1:
        inicio = 0
    else:
        inicio += 1

    fim = codigo.find("\n", posicao)

    if fim == -1:
        fim = len(codigo)

    return codigo[inicio:fim].strip()


def _normalizar_biblioteca(pacote: str) -> str:
    """
    Converte um caminho de pacote em seu nome-base.

    Exemplos:
        lodash/debounce -> lodash
        axios/lib/core -> axios
        @scope/pkg/submodule -> @scope/pkg
    """
    valor = pacote.strip()

    if not valor:
        return ""

    if (
        valor.startswith("./")
        or valor.startswith("../")
        or valor.startswith("/")
        or valor.startswith("file:")
        or valor.startswith("http:")
        or valor.startswith("https:")
    ):
        return ""

    partes = valor.split("/")

    if valor.startswith("@"):
        if len(partes) < 2:
            return ""

        return "/".join(partes[:2])

    return partes[0]


def _confianca(pontuacao: int) -> str:
    if pontuacao >= 90:
        return "ALTA"

    if pontuacao >= 75:
        return "MEDIA"

    return "BAIXA"


def _criar_observacao(
    *,
    biblioteca: str,
    origem: str | None,
    arquivo: str | None,
    tipo: str,
    localizacao: dict[str, int],
    evidencia: str,
    linguagem: str,
) -> dict[str, Any]:
    pontuacao = 95

    return {
        "biblioteca": biblioteca,
        "origem": origem,
        "arquivo": arquivo,
        "tipo": tipo,
        "localizacao": localizacao,
        "evidencias": [
            {
                "tipo": tipo,
                "valor": evidencia,
                "localizacao": localizacao,
            }
        ],
        "pontuacao": pontuacao,
        "confianca": _confianca(pontuacao),
        "linguagem": linguagem,
    }


def detectar_bibliotecas(
    codigo: str,
    *,
    origem: str | None = None,
    arquivo: str | None = None,
    linguagem: str = "javascript",
) -> list[dict[str, Any]]:
    """
    Detecta bibliotecas/pacotes explicitamente referenciados no código.

    Retorna uma observação por biblioteca única dentro do código analisado.
    """
    if not codigo:
        return []

    linguagem_normalizada = _normalizar_linguagem(linguagem)

    if not _linguagem_suportada(linguagem_normalizada):
        return []

    codigo_sem_comentarios = _mascarar_comentarios(codigo)
    codigo_mascarado = _mascarar_codigo(codigo)

    observacoes: list[dict[str, Any]] = []
    por_biblioteca: dict[str, dict[str, Any]] = {}

    ocorrencias: list[tuple[int, str, str]] = []

    for tipo, padrao in _PADROES_IMPORTACAO:
        for correspondencia in padrao.finditer(codigo_sem_comentarios):
            inicio = correspondencia.start()

            if _esta_em_string(codigo_mascarado, inicio):
                continue

            pacote = correspondencia.group("pacote")
            biblioteca = _normalizar_biblioteca(pacote)

            if not biblioteca:
                continue

            ocorrencias.append(
                (
                    inicio,
                    tipo,
                    biblioteca,
                )
            )

    ocorrencias.sort(key=lambda item: item[0])

    for inicio, tipo, biblioteca in ocorrencias:
        evidencia = _evidencia(codigo, inicio)
        localizacao = _localizacao(codigo, inicio)

        observacao = por_biblioteca.get(biblioteca)

        if observacao is None:
            observacao = _criar_observacao(
                biblioteca=biblioteca,
                origem=origem,
                arquivo=arquivo,
                tipo=tipo,
                localizacao=localizacao,
                evidencia=evidencia,
                linguagem=linguagem_normalizada,
            )

            por_biblioteca[biblioteca] = observacao
            observacoes.append(observacao)
            continue

        observacao["evidencias"].append(
            {
                "tipo": tipo,
                "valor": evidencia,
                "localizacao": localizacao,
            }
        )

    return observacoes
