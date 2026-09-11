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



def _extrair_contextos(
    codigo: str,
    padrao: str,
    linhas_contexto: int,
) -> list[dict]:
    """
    Localiza ocorrências de um padrão e retorna a linha encontrada
    juntamente com algumas linhas ao redor.

    A análise é puramente estática:
    o JavaScript não é executado.
    """

    regex = re.compile(
        padrao,
        flags=re.IGNORECASE,
    )

    linhas = codigo.splitlines()
    ocorrencias = []

    for indice, linha in enumerate(linhas):
        if not regex.search(linha):
            continue

        inicio = max(
            0,
            indice - linhas_contexto,
        )

        fim = min(
            len(linhas),
            indice + linhas_contexto + 1,
        )

        contexto = []

        for numero in range(inicio, fim):
            contexto.append(
                {
                    "linha": numero + 1,
                    "conteudo": linhas[numero],
                }
            )

        ocorrencias.append(
            {
                "linha": indice + 1,
                "contexto": contexto,
            }
        )

    return ocorrencias


def _analisar_padroes_sensiveis(codigo: str) -> dict[str, list[dict]]:
    """
    Procura padrões relevantes para análise estática de JavaScript.

    A presença de um padrão não significa, por si só, que exista
    uma vulnerabilidade. O resultado serve como evidência para
    análise e correlação posteriores.
    """

    padroes = {
        "document_cookie": {
            "padrao": r"\bdocument\.cookie\b",
            "linhas_contexto": 3,
        },
        "local_storage": {
            "padrao": r"\blocalStorage\b",
            "linhas_contexto": 3,
        },
        "session_storage": {
            "padrao": r"\bsessionStorage\b",
            "linhas_contexto": 3,
        },
        "new_function": {
            "padrao": r"\bnew\s+Function\b",
            "linhas_contexto": 3,
        },
        "xmlhttprequest": {
            "padrao": r"\bXMLHttpRequest\b",
            "linhas_contexto": 3,
        },
        "wss_live_publisher": {
            "padrao": (
                r"wss://live-publisher-api\.premierbet\.co\.ao/v1"
            ),
            "linhas_contexto": 5,
        },
        "websocket": {
            "padrao": r"\bWebSocket\b",
            "linhas_contexto": 5,
        },
    }

    resultado = {}

    for nome, configuracao in padroes.items():
        ocorrencias = _extrair_contextos(
            codigo,
            configuracao["padrao"],
            configuracao["linhas_contexto"],
        )

        resultado[nome] = ocorrencias

    return resultado


def _analisar_dom_sinks(codigo: str) -> list[dict[str, Any]]:
    """
    Detecta sinks de DOM por análise estática.

    A detecção representa apenas um ponto potencial de
    consumo de dados no DOM. Não confirma vulnerabilidade.
    """
    padroes = [
        (r"\.innerHTML\s*=", "innerHTML"),
        (r"\.outerHTML\s*=", "outerHTML"),
        (r"\.insertAdjacentHTML\s*\(", "insertAdjacentHTML"),
        (r"\bdocument\.write(?:ln)?\s*\(", "document.write"),
    ]

    resultado = []

    for padrao, tipo in padroes:
        contextos = _extrair_contextos(
            codigo,
            padrao,
            linhas_contexto=0,
        )

        for item in contextos:
            resultado.append(
                {
                    "tipo": tipo,
                    "linha": item["linha"],
                    "conteudo": item["contexto"][0]["conteudo"],
                }
            )

    resultado.sort(key=lambda item: item["linha"])

    return resultado


def _analisar_fontes_dados(codigo: str) -> list[dict[str, Any]]:
    """
    Detecta fontes de dados relevantes por análise estática.

    A análise identifica apenas padrões sintáticos.
    Não executa o código nem confirma que os dados sejam
    controláveis por um usuário externo.
    """
    resultado = []

    # Identifica variáveis que recebem XMLHttpRequest.
    xhr_variaveis = set(
        re.findall(
            r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*="
            r"\s*new\s+XMLHttpRequest\s*\(",
            codigo,
        )
    )

    for variavel in sorted(xhr_variaveis):
        padroes = [
            (
                rf"\b{re.escape(variavel)}\.response\b",
                "XMLHttpRequest.response",
            ),
            (
                rf"\b{re.escape(variavel)}\.responseText\b",
                "XMLHttpRequest.responseText",
            ),
        ]

        for padrao, tipo in padroes:
            contextos = _extrair_contextos(
                codigo,
                padrao,
                linhas_contexto=0,
            )

            for item in contextos:
                resultado.append(
                    {
                        "tipo": tipo,
                        "linha": item["linha"],
                        "conteudo": item["contexto"][0]["conteudo"],
                    }
                )

    # fetch() é registrado como fonte de dados candidata.
    contextos_fetch = _extrair_contextos(
        codigo,
        r"\bfetch\s*\(",
        linhas_contexto=0,
    )

    for item in contextos_fetch:
        resultado.append(
            {
                "tipo": "fetch",
                "linha": item["linha"],
                "conteudo": item["contexto"][0]["conteudo"],
            }
        )

    resultado.sort(key=lambda item: item["linha"])

    return resultado




def _linha_do_codigo(codigo: str, posicao: int) -> int:
    return codigo.count("\n", 0, posicao) + 1


def _sanitizar_valor_http(valor: str) -> str:
    valor = valor.strip()

    if (
        len(valor) >= 2
        and valor[0] == valor[-1]
        and valor[0] in {"\"", "'", "`"}
    ):
        valor = valor[1:-1].strip()

    if not valor:
        return ""

    padroes_sensiveis = (
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "token",
        "access_token",
        "refresh_token",
        "id_token",
        "bearer",
        "api-key",
        "apikey",
        "secret",
        "password",
        "passwd",
    )

    valor_lower = valor.lower()

    if any(
        padrao in valor_lower
        for padrao in padroes_sensiveis
    ):
        return "[VALOR_REDACTED]"

    return valor


def _extrair_headers_http(bloco: str) -> list[dict]:
    resultado = []

    padrao_objeto = re.compile(
        r"""headers\s*:\s*\{([\s\S]{0,4000}?)\}""",
        flags=re.IGNORECASE | re.MULTILINE,
    )

    padrao_pares = re.compile(
        r"""["'`]([^"'`]+)["'`]\s*:\s*([^,}\n]+)""",
        flags=re.IGNORECASE | re.MULTILINE,
    )

    for objeto in padrao_objeto.finditer(bloco):
        conteudo_headers = objeto.group(1)

        for correspondencia in padrao_pares.finditer(conteudo_headers):
            nome = correspondencia.group(1).strip()
            valor = correspondencia.group(2).strip()

            if not nome:
                continue

            resultado.append(
                {
                    "nome": nome,
                    "valor": _sanitizar_valor_http(valor),
                }
            )

    padrao_xhr = re.compile(
        r"""\bsetRequestHeader\s*\(\s*["'`]([^"'`]+)["'`]\s*,\s*([^,)]+)""",
        flags=re.IGNORECASE | re.MULTILINE,
    )

    for correspondencia in padrao_xhr.finditer(bloco):
        nome = correspondencia.group(1).strip()
        valor = correspondencia.group(2).strip()

        if not nome:
            continue

        resultado.append(
            {
                "nome": nome,
                "valor": _sanitizar_valor_http(valor),
            }
        )

    unicos = []
    vistos = set()

    for header in resultado:
        chave = (
            header["nome"].lower(),
            header["valor"],
        )

        if chave in vistos:
            continue

        vistos.add(chave)
        unicos.append(header)

    return unicos


def _extrair_body_http(bloco: str) -> str:
    padroes = [
        r"""\bbody\s*:\s*([^,}\n]+)""",
        r"""\.send\s*\(([^)]*)\)""",
    ]

    for padrao in padroes:
        correspondencia = re.search(
            padrao,
            bloco,
            flags=re.IGNORECASE | re.MULTILINE,
        )

        if correspondencia:
            return _sanitizar_valor_http(
                correspondencia.group(1)
            )

    return ""


def _analisar_requisicoes_http(codigo: str) -> list[dict]:
    resultado = []

    # ---------------------------------------------------------
    # FETCH
    # ---------------------------------------------------------
    padrao_fetch = re.compile(
        r"""\bfetch\s*\(\s*"""
        r"""["'`]([^"'`]+)["'`]"""
        r"""([\s\S]{0,1200}?)"""
        r"""\)""",
        flags=re.IGNORECASE | re.MULTILINE,
    )

    for correspondencia in padrao_fetch.finditer(codigo):
        url = correspondencia.group(1).strip()
        bloco = correspondencia.group(0)
        inicio = correspondencia.start()

        metodo = "GET"

        metodo_match = re.search(
            r"""\bmethod\s*:\s*["'`]([A-Za-z]+)["'`]""",
            bloco,
            flags=re.IGNORECASE,
        )

        if metodo_match:
            metodo = metodo_match.group(1).upper()

        resultado.append({
            "tipo": "fetch",
            "metodo": metodo,
            "url": url,
            "headers": _extrair_headers_http(bloco),
            "body": _extrair_body_http(bloco),
            "linha": _linha_do_codigo(codigo, inicio),
        })

    # ---------------------------------------------------------
    # XMLHttpRequest
    # ---------------------------------------------------------
    variaveis_xhr = {}

    for correspondencia in re.finditer(
        r"""\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)"""
        r"""\s*=\s*new\s+XMLHttpRequest\s*\(\s*\)""",
        codigo,
        flags=re.IGNORECASE | re.MULTILINE,
    ):
        variaveis_xhr[correspondencia.group(1)] = (
            correspondencia.start()
        )

    for nome_variavel, inicio_variavel in variaveis_xhr.items():
        fim_contexto = min(
            len(codigo),
            inicio_variavel + 2500,
        )

        bloco = codigo[
            inicio_variavel:fim_contexto
        ]

        open_match = re.search(
            rf"""\b{re.escape(nome_variavel)}\s*\.\s*open\s*\("""
            r"""\s*["'`]([A-Za-z]+)["'`]"""
            r"""\s*,\s*["'`]([^"'`]+)["'`]""",
            bloco,
            flags=re.IGNORECASE | re.MULTILINE,
        )

        if not open_match:
            continue

        metodo = open_match.group(1).upper()
        url = open_match.group(2).strip()

        headers = []

        for header_match in re.finditer(
            rf"""\b{re.escape(nome_variavel)}\s*\.\s*"""
            r"""setRequestHeader\s*\("""
            r"""\s*["'`]([^"'`]+)["'`]"""
            r"""\s*,\s*([^)]*)\)""",
            bloco,
            flags=re.IGNORECASE | re.MULTILINE,
        ):
            headers.append({
                "nome": header_match.group(1).strip(),
                "valor": _sanitizar_valor_http(
                    header_match.group(2)
                ),
            })

        send_match = re.search(
            rf"""\b{re.escape(nome_variavel)}\s*\.\s*"""
            r"""send\s*\(([^)]*)\)""",
            bloco,
            flags=re.IGNORECASE | re.MULTILINE,
        )

        body = ""

        if send_match:
            body = _sanitizar_valor_http(
                send_match.group(1)
            )

        resultado.append({
            "tipo": "xmlhttprequest",
            "metodo": metodo,
            "url": url,
            "headers": headers,
            "body": body,
            "linha": _linha_do_codigo(
                codigo,
                inicio_variavel + open_match.start(),
            ),
        })

    # ---------------------------------------------------------
    # AXIOS
    # ---------------------------------------------------------
    padrao_axios = re.compile(
        r"""\baxios\."""
        r"""(get|post|put|patch|delete|head|options)\s*\("""
        r"""\s*["'`]([^"'`]+)["'`]"""
        r"""([\s\S]{0,1200}?)"""
        r"""\)""",
        flags=re.IGNORECASE | re.MULTILINE,
    )

    for correspondencia in padrao_axios.finditer(codigo):
        metodo = correspondencia.group(1).upper()
        url = correspondencia.group(2).strip()
        bloco = correspondencia.group(0)

        body = ""

        argumentos = bloco.split(
            ",",
            2,
        )

        if len(argumentos) >= 2:
            segundo = argumentos[1].strip()

            if segundo:
                body = _sanitizar_valor_http(
                    segundo
                )

        resultado.append({
            "tipo": "axios",
            "metodo": metodo,
            "url": url,
            "headers": _extrair_headers_http(bloco),
            "body": body,
            "linha": _linha_do_codigo(
                codigo,
                correspondencia.start(),
            ),
        })

    resultado.sort(
        key=lambda item: (
            item["linha"],
            item["tipo"],
            item["metodo"],
            item["url"],
        )
    )

    return resultado

def _analisar_inspecao_profunda(codigo: str) -> dict:
    """
    Executa uma inspeção estática mais ampla do JavaScript.

    Equivale, dentro do analisador, às inspeções que normalmente
    seriam feitas manualmente com curl, head e grep.

    O código não é executado e nenhuma requisição é realizada.
    """

    if not codigo:
        return {
            "tamanho_bytes": 0,
            "inicio_codigo": "",
            "urls_http": [],
            "urls_websocket": [],
            "metodos_http": {},
            "indicadores_sensiveis": {},
            "resumo": {
                "urls_http": 0,
                "urls_websocket": 0,
                "metodos_http": 0,
                "indicadores_sensiveis": 0,
            },
        }

    # Equivalente estático a:
    # wc -c
    tamanho_bytes = len(
        codigo.encode("utf-8")
    )

    # Equivalente seguro a:
    # head -c 500
    inicio_codigo = codigo[:500]

    # URLs HTTP/HTTPS.
    urls_http = _encontrar_unicos(
        r"""https?://[^"'`\s)]+""",
        codigo,
    )

    # URLs WebSocket.
    urls_websocket = _encontrar_unicos(
        r"""wss?://[^"'`\s)]+""",
        codigo,
    )

    # Métodos HTTP.
    metodos = [
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ]

    metodos_http = {}

    for metodo in metodos:
        ocorrencias = re.findall(
            rf"""["']{metodo}["']""",
            codigo,
            flags=re.IGNORECASE,
        )

        if ocorrencias:
            metodos_http[metodo] = len(
                ocorrencias
            )

    # Também reconhece:
    # xhr.open("GET", ...)
    # mesmo quando a contagem anterior já encontrou o método.
    #
    # Mantemos uma contagem única das ocorrências literais
    # para não inventar chamadas que não estejam no código.

    indicadores = {
        "localStorage": r"\blocalStorage\b",
        "sessionStorage": r"\bsessionStorage\b",
        "document.cookie": r"\bdocument\.cookie\b",
        "Authorization": r"\bAuthorization\b",
        "Bearer": r"\bBearer\b",
        "WebSocket": r"\bWebSocket\b",
        "XMLHttpRequest": r"\bXMLHttpRequest\b",
    }

    indicadores_sensiveis = {}

    for nome, padrao in indicadores.items():
        ocorrencias = _extrair_contextos(
            codigo,
            padrao,
            2,
        )

        if ocorrencias:
            indicadores_sensiveis[nome] = {
                "quantidade": len(ocorrencias),
                "ocorrencias": ocorrencias,
            }

    quantidade_indicadores = sum(
        item["quantidade"]
        for item in indicadores_sensiveis.values()
    )

    return {
        "tamanho_bytes": tamanho_bytes,
        "inicio_codigo": inicio_codigo,
        "urls_http": urls_http,
        "urls_websocket": urls_websocket,
        "metodos_http": metodos_http,
        "indicadores_sensiveis": indicadores_sensiveis,
        "resumo": {
            "urls_http": len(urls_http),
            "urls_websocket": len(urls_websocket),
            "metodos_http": sum(
                metodos_http.values()
            ),
            "indicadores_sensiveis": quantidade_indicadores,
        },
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
            "requisicoes_http": [],
            "apis": {
                "fetch": [],
                "xmlhttprequest": [],
                "axios": [],
            },
            "frameworks": [],
            "padroes_sensiveis": {
                "document_cookie": [],
                "local_storage": [],
                "session_storage": [],
                "new_function": [],
                "xmlhttprequest": [],
                "wss_live_publisher": [],
                "websocket": [],
            },
            "inspecao_profunda": {
                "tamanho_bytes": 0,
                "inicio_codigo": "",
                "urls_http": [],
                "urls_websocket": [],
                "metodos_http": {},
                "indicadores_sensiveis": {},
                "resumo": {
                    "urls_http": 0,
                    "urls_websocket": 0,
                    "metodos_http": 0,
                    "indicadores_sensiveis": 0,
                },
            },
            "caracteristicas": {
                "usa_fetch": False,
                "usa_xhr": False,
                "usa_websocket": False,
                "usa_modules": False,
                "usa_async": False,
            },
        }

    dom_sinks = _analisar_dom_sinks(codigo)
    fontes_dados = _analisar_fontes_dados(codigo)
    requisicoes_http = _analisar_requisicoes_http(codigo)

    return {
        "dom_sinks": dom_sinks,
        "fontes_dados": fontes_dados,
        "detectado": True,
        "tamanho": len(codigo),
        "funcoes": _analisar_funcoes(codigo),
        "imports": _analisar_imports(codigo),
        "exports": _analisar_exports(codigo),
        "urls": _analisar_urls(codigo),
        "endpoints": _analisar_endpoints(codigo),
        "websockets": _analisar_websockets(codigo),
        "requisicoes_http": requisicoes_http,
        "apis": _analisar_apis(codigo),
        "frameworks": _detectar_frameworks(codigo),
        "padroes_sensiveis": _analisar_padroes_sensiveis(codigo),
        "inspecao_profunda": _analisar_inspecao_profunda(codigo),
        "caracteristicas": _detectar_caracteristicas(codigo),
    }
