from __future__ import annotations

import base64
import binascii
import re
from urllib.parse import unquote


def decodificar_escapes_javascript(texto: str) -> str:
    """
    Decodifica escapes comuns de JavaScript:
    \\xHH
    \\uHHHH
    """
    if not texto:
        return ""

    def substituir_unicode(match: re.Match[str]) -> str:
        try:
            return chr(int(match.group(1), 16))
        except ValueError:
            return match.group(0)

    def substituir_hex(match: re.Match[str]) -> str:
        try:
            return chr(int(match.group(1), 16))
        except ValueError:
            return match.group(0)

    resultado = re.sub(
        r"\\u([0-9a-fA-F]{4})",
        substituir_unicode,
        texto,
    )

    resultado = re.sub(
        r"\\x([0-9a-fA-F]{2})",
        substituir_hex,
        resultado,
    )

    return resultado


def decodificar_url(texto: str) -> str:
    """Decodifica percent-encoding de URL."""
    if not texto:
        return ""

    return unquote(texto)


def decodificar_base64(texto: str) -> str | None:
    """
    Tenta decodificar Base64.

    Retorna None quando o conteúdo não parece ser
    Base64 válido ou não resulta em texto UTF-8.
    """
    if not texto:
        return None

    valor = texto.strip()

    if len(valor) < 4:
        return None

    if not re.fullmatch(
        r"[A-Za-z0-9+/]+={0,2}",
        valor,
    ):
        return None

    if len(valor) % 4 != 0:
        return None

    try:
        dados = base64.b64decode(
            valor,
            validate=True,
        )
        return dados.decode("utf-8")
    except (
        ValueError,
        binascii.Error,
        UnicodeDecodeError,
    ):
        return None


def decodificar_hex(texto: str) -> str | None:
    """
    Tenta interpretar uma string hexadecimal como texto UTF-8.
    """
    if not texto:
        return None

    valor = texto.strip()

    if len(valor) < 2 or len(valor) % 2 != 0:
        return None

    if not re.fullmatch(
        r"[0-9a-fA-F]+",
        valor,
    ):
        return None

    try:
        dados = bytes.fromhex(valor)
        return dados.decode("utf-8")
    except (
        ValueError,
        UnicodeDecodeError,
    ):
        return None


def decodificar_javascript(texto: str) -> dict:
    """
    Executa apenas transformações estáticas sobre texto.

    Nenhum JavaScript é executado.
    Nenhuma requisição de rede é realizada.
    """
    original = texto or ""

    resultado = {
        "original": original,
        "escapes": decodificar_escapes_javascript(
            original
        ),
        "url": decodificar_url(original),
        "base64": decodificar_base64(original),
        "hex": decodificar_hex(original),
    }

    return resultado
def extrair_strings_javascript(
    codigo: str,
) -> list[str]:
    """
    Extrai strings literais simples de JavaScript.

    Suporta strings delimitadas por:
    - aspas simples: 'texto'
    - aspas duplas: "texto"

    Não executa JavaScript.
    """
    if not codigo:
        return []

    padrao = re.compile(
        r"""(["'])(.*?)(?<!\\)\1""",
        re.DOTALL,
    )

    resultados = []

    for _, conteudo in padrao.findall(codigo):
        if conteudo:
            resultados.append(conteudo)

    return resultados

    for _, conteudo in padrao.findall(codigo):
        if conteudo:
            resultados.append(conteudo)

    return resultados
