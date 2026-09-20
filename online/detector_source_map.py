from __future__ import annotations

import re

from .source_map import (
    classificar_referencia_source_map,
    normalizar_referencia_source_map,
    resolver_url_source_map,
)


_PADRAO_SOURCE_MAP = re.compile(
    r"(?m)^[ \t]*//[ \t]*[#@][ \t]*sourceMappingURL[ \t]*="
    r"[ \t]*([^\s]+)[ \t]*$"
)


def detectar_source_maps(
    codigo: str,
    origem: str = "",
    arquivo: str = "",
    script_url: str = "",
    linguagem: str = "javascript",
) -> list[dict]:
    """Detecta referências declaradas a Source Maps no código JavaScript."""
    if not codigo:
        return []

    resultados = []

    for ocorrencia in _PADRAO_SOURCE_MAP.finditer(codigo):
        referencia = normalizar_referencia_source_map(
            ocorrencia.group(1)
        )

        if not referencia:
            continue

        linha = codigo.count(
            "\n",
            0,
            ocorrencia.start(),
        ) + 1

        evidencia = ocorrencia.group(0).strip()

        resultados.append({
            "origem": origem,
            "arquivo": arquivo,
            "script_url": script_url,
            "referencia": referencia,
            "url": resolver_url_source_map(
                referencia,
                script_url or arquivo,
            ),
            "tipo": classificar_referencia_source_map(
                referencia
            ),
            "linha": linha,
            "evidencia": evidencia,
            "classificacao": "SOURCE_MAP_REFERENCIA",
            "confianca": "ALTA",
            "linguagem": linguagem,
        })

    return resultados
