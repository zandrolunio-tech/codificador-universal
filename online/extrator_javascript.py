from __future__ import annotations

import re
from html import unescape
from urllib.parse import urljoin

from .modelos import JavaScriptExtraido


def _extrair_atributos(tag: str) -> dict[str, str]:
    atributos = {}

    padrao = re.compile(
        r"""([:\w-]+)\s*=\s*["']([^"']*)["']""",
        re.IGNORECASE,
    )

    for nome, valor in padrao.findall(tag):
        atributos[nome.lower()] = unescape(valor)

    return atributos


def _normalizar_url(url: str, base_url: str) -> str:
    return urljoin(base_url, url)


def extrair_javascript(
    html: str,
    base_url: str = "",
) -> list[JavaScriptExtraido]:
    """
    Extrai referências e blocos JavaScript de um documento HTML.

    A função é exclusivamente estática:
    - não executa JavaScript;
    - não realiza requisições;
    - não baixa arquivos externos;
    - não modifica o HTML original.

    Detecta:
    - <script src="...">
    - <script type="module" src="...">
    - JavaScript inline;
    - módulos inline;
    - atributos relevantes do elemento script.
    """

    if not html:
        return []

    resultados: list[JavaScriptExtraido] = []

    padrao_script = re.compile(
        r"<script\b([^>]*)>(.*?)</script\s*>",
        re.IGNORECASE | re.DOTALL,
    )

    for atributos_brutos, conteudo in padrao_script.findall(html):
        tag = f"<script{atributos_brutos}>"

        atributos = _extrair_atributos(tag)

        src = atributos.get("src", "")
        tipo = atributos.get("type", "").lower()

        if src:
            url = _normalizar_url(
                src,
                base_url,
            )

            resultados.append(
                JavaScriptExtraido(
                    origem="script_src",
                    tipo=(
                        "module"
                        if tipo == "module"
                        else "externo"
                    ),
                    conteudo="",
                    url=url,
                    atributos=atributos,
                )
            )

            continue

        conteudo_limpo = conteudo.strip()

        if not conteudo_limpo:
            continue

        resultados.append(
            JavaScriptExtraido(
                origem="script_inline",
                tipo=(
                    "module"
                    if tipo == "module"
                    else "inline"
                ),
                conteudo=conteudo_limpo,
                url=base_url,
                atributos=atributos,
            )
        )

    return resultados


def extrair_urls_javascript(
    html: str,
    base_url: str = "",
) -> list[str]:
    """
    Retorna somente as URLs de scripts externos encontrados
    no HTML.
    """

    scripts = extrair_javascript(
        html,
        base_url=base_url,
    )

    return sorted(
        {
            script.url
            for script in scripts
            if script.url
            and script.origem == "script_src"
        }
    )


def extrair_codigo_inline(
    html: str,
) -> list[str]:
    """
    Retorna somente os blocos JavaScript inline.
    """

    scripts = extrair_javascript(html)

    return [
        script.conteudo
        for script in scripts
        if script.origem == "script_inline"
        and script.conteudo
    ]
