from __future__ import annotations

from .decodificador_javascript import (
    decodificar_escapes_javascript,
    decodificar_url,
    decodificar_base64,
    decodificar_hex,
)


def normalizar_string_javascript(
    valor: str,
) -> dict:
    """
    Normaliza estaticamente uma string JavaScript.

    Mantém o valor original e registra as transformações
    aplicadas.

    Não executa JavaScript.
    Não realiza requisições de rede.
    """
    original = valor or ""

    if not original:
        return {
            "original": "",
            "normalizado": "",
            "transformacoes": [],
        }

    atual = original
    transformacoes = []

    # 1. Escapes JavaScript
    resultado = decodificar_escapes_javascript(atual)

    if resultado != atual:
        atual = resultado
        transformacoes.append(
            "escape_javascript"
        )

    # 2. URL encoding
    resultado = decodificar_url(atual)

    if resultado != atual:
        atual = resultado
        transformacoes.append(
            "url_decode"
        )

    # 3. Base64
    resultado_base64 = decodificar_base64(atual)

    if resultado_base64 is not None:
        if resultado_base64 != atual:
            atual = resultado_base64
            transformacoes.append(
                "base64"
            )

    # 4. Hexadecimal
    resultado_hex = decodificar_hex(atual)

    if resultado_hex is not None:
        if resultado_hex != atual:
            atual = resultado_hex
            transformacoes.append(
                "hex"
            )

    return {
        "original": original,
        "normalizado": atual,
        "transformacoes": transformacoes,
    }
