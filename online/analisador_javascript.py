from __future__ import annotations

import re
from urllib.parse import urlparse


def _encontrar_unicos(padrao: str, codigo: str) -> list[str]:
    encontrados = re.findall(
        padrao,
        codigo,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    resultado = []

    for item in encontrados:
        if isinstance(item, tuple):
            item = next(
                (valor for valor in item if valor),
                "",
            )

        item = item.strip()

        if item and item not in resultado:
            resultado.append(item)

    return sorted(resultado)


def _analisar_funcoes(codigo: str) -> list[str]:
    padroes = [
        r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(",
        r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(",
        r"\b([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
    ]

    resultado = []

    for padrao in padroes:
        resultado.extend(
            _encontrar_unicos(
                padrao,
                codigo,
            )
        )

    return sorted(set(resultado))


def _analisar_imports(codigo: str) -> list[str]:
    padroes = [
        r"\bimport\s+(?:[^;]*?\s+from\s+)?[\"']([^\"']+)[\"']",
        r"\bimport\s*\(\s*[\"']([^\"']+)[\"']\s*\)",
    ]

    resultado = []

    for padrao in padroes:
        resultado.extend(
            _encontrar_unicos(
                padrao,
                codigo,
            )
        )

    return sorted(set(resultado))


def _analisar_exports(codigo: str) -> list[str]:
    padroes = [
        r"\bexport\s+(?:default\s+)?(?:function|class|const|let|var)\s+([A-Za-z_$][\w$]*)",
        r"\bexport\s*\{\s*([^}]+)\s*\}",
    ]

    resultado = []

    for padrao in padroes:
        encontrados = re.findall(
            padrao,
            codigo,
            flags=re.IGNORECASE | re.MULTILINE,
        )

        for item in encontrados:
            partes = re.split(
                r",",
                item,
            )

            for parte in partes:
                nome = parte.strip()

                if nome:
                    nome = nome.split(
                        " as ",
                        1,
                    )[0].strip()

                    if nome and nome not in resultado:
                        resultado.append(nome)

    return sorted(set(resultado))


def _analisar_urls(codigo: str) -> list[str]:
    padrao = (
        r"""["'`]"""
        r"""((?:https?:\/\/|wss?:\/\/)[^"'`\s]+)"""
        r"""["'`]"""
    )

    encontrados = _encontrar_unicos(
        padrao,
        codigo,
    )

    resultado = []

    for url in encontrados:
        try:
            parsed = urlparse(url)

            if parsed.scheme and parsed.netloc:
                resultado.append(url)
        except ValueError:
            continue

    return sorted(set(resultado))


def _analisar_endpoints(codigo: str) -> list[str]:
    padrao = (
        r"""["'`]"""
        r"""(\/(?:api|v[0-9]+|graphql|rest|auth|login|logout)"""
        r"""(?:\/[A-Za-z0-9_.$~%:+\-{}]+)*)"""
        r"""["'`]"""
    )

    return _encontrar_unicos(
        padrao,
        codigo,
    )


def _analisar_websockets(codigo: str) -> list[str]:
    padrao = (
        r"""["'`]"""
        r"""((?:wss?|ws):\/\/[^"'`\s]+)"""
        r"""["'`]"""
    )

    return _encontrar_unicos(
        padrao,
        codigo,
    )


def _analisar_apis(codigo: str) -> dict[str, list[str]]:
    fetches = _encontrar_unicos(
        r"\bfetch\s*\(\s*[\"'`]([^\"'`]+)",
        codigo,
    )

    xhr = _encontrar_unicos(
        r"""\.open\s*\(\s*[\"'][A-Z]+[\"']\s*,\s*[\"']([^\"']+)""",
        codigo,
    )

    axios = _encontrar_unicos(
        r"""\baxios\.(?:get|post|put|patch|delete)\s*\(\s*[\"'`]([^\"'`]+)""",
        codigo,
    )

    return {
        "fetch": fetches,
        "xmlhttprequest": xhr,
        "axios": axios,
    }


def _detectar_frameworks(codigo: str) -> list[str]:
    indicadores = {
        "react": [
            r"\bReact\b",
            r"\bReactDOM\b",
            r"from\s+[\"']react[\"']",
        ],
        "vue": [
            r"\bVue\b",
            r"from\s+[\"']vue[\"']",
        ],
        "angular": [
            r"\bNgModule\b",
            r"\bComponent\b",
            r"from\s+[\"']@angular/",
        ],
        "next.js": [
            r"from\s+[\"']next/",
            r"\bNextJS\b",
        ],
        "nuxt": [
            r"from\s+[\"']nuxt",
        ],
        "jquery": [
            r"\bjQuery\b",
            r"\$\s*\(",
        ],
        "svelte": [
            r"from\s+[\"']svelte[\"']",
        ],
    }

    encontrados = []

    for nome, padroes in indicadores.items():
        for padrao in padroes:
            if re.search(
                padrao,
                codigo,
                flags=re.IGNORECASE,
            ):
                encontrados.append(nome)
                break

    return sorted(set(encontrados))


def _detectar_caracteristicas(codigo: str) -> dict[str, bool]:
    return {
        "usa_fetch": bool(
            re.search(
                r"\bfetch\s*\(",
                codigo,
                re.IGNORECASE,
            )
        ),
        "usa_xhr": bool(
            re.search(
                r"\bXMLHttpRequest\b",
                codigo,
                re.IGNORECASE,
            )
        ),
        "usa_websocket": bool(
            re.search(
                r"\bWebSocket\s*\(",
                codigo,
                re.IGNORECASE,
            )
        ),
        "usa_modules": bool(
            re.search(
                r"\b(?:import|export)\b",
                codigo,
                re.IGNORECASE,
            )
        ),
        "usa_async": bool(
            re.search(
                r"\basync\b|\bawait\b",
                codigo,
                re.IGNORECASE,
            )
        ),
    }


def analisar_javascript(codigo: str) -> dict:
    """
    Analisa estruturalmente código JavaScript.

    A função não executa o código e não realiza requisições.
    """

    if not isinstance(codigo, str):
        raise TypeError(
            "codigo deve ser uma string."
        )

    codigo = codigo.strip()

    if not codigo:
        return {
            "detectado": False,
            "tamanho": 0,
            "funcoes": [],
            "imports": [],
            "exports": [],
            "urls": [],
            "endpoints": [],
            "websockets": [],
            "apis": {
                "fetch": [],
                "xmlhttprequest": [],
                "axios": [],
            },
            "frameworks": [],
            "caracteristicas": {
                "usa_fetch": False,
                "usa_xhr": False,
                "usa_websocket": False,
                "usa_modules": False,
                "usa_async": False,
            },
        }

    return {
        "detectado": True,
        "tamanho": len(codigo),
        "funcoes": _analisar_funcoes(codigo),
        "imports": _analisar_imports(codigo),
        "exports": _analisar_exports(codigo),
        "urls": _analisar_urls(codigo),
        "endpoints": _analisar_endpoints(codigo),
        "websockets": _analisar_websockets(codigo),
        "apis": _analisar_apis(codigo),
        "frameworks": _detectar_frameworks(codigo),
        "caracteristicas": _detectar_caracteristicas(codigo),
    }
